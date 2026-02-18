"""
Triage scoring engine - calculates priority scores with explainability.

Score components:
1. Severity weight (base score from highest severity alert)
2. Entity frequency (how often entities appear in other alerts)
3. Risk indicators (suspicious patterns)
"""
from typing import List, Dict, Set, Tuple, Any
from sqlalchemy.orm import Session
from models import Alert, Severity


# Severity base scores
SEVERITY_SCORES = {
    Severity.CRITICAL: 40,
    Severity.HIGH: 30,
    Severity.MEDIUM: 20,
    Severity.LOW: 10,
}

# Entity frequency thresholds
ENTITY_FREQUENCY_THRESHOLD = 3  # Number of alerts with same entity to trigger bonus


def calculate_severity_score(alerts: List[Alert]) -> Tuple[float, str]:
    """Calculate score based on alert severities."""
    if not alerts:
        return 0, "No alerts"
    
    # Get maximum severity
    max_severity = max(alerts, key=lambda a: SEVERITY_SCORES.get(a.severity, 0))
    score = SEVERITY_SCORES.get(max_severity.severity, 0)
    
    # Bonus for multiple high/critical alerts
    critical_count = sum(1 for a in alerts if a.severity == Severity.CRITICAL)
    high_count = sum(1 for a in alerts if a.severity == Severity.HIGH)
    
    bonus = (critical_count * 5) + (high_count * 2)
    
    reason = f"Highest severity: {max_severity.severity.value}"
    if critical_count > 1:
        reason += f", {critical_count} critical alerts (+{critical_count * 5})"
    if high_count > 1:
        reason += f", {high_count} high alerts (+{high_count * 2})"
    
    return score + bonus, reason


def calculate_entity_frequency_score(
    alerts: List[Alert],
    entities: Dict[str, Set[str]],
    db: Session
) -> Tuple[float, str]:
    """Calculate score based on entity frequency across all alerts."""
    score = 0
    reasons = []
    
    # Check each entity type
    for entity_type, entity_values in entities.items():
        for entity_value in entity_values:
            if not entity_value:
                continue
            
            # Count occurrences in database
            if entity_type == "users":
                count = db.query(Alert).filter(Alert.entity_user == entity_value).count()
                if count >= ENTITY_FREQUENCY_THRESHOLD:
                    score += 10
                    reasons.append(f"User '{entity_value}' in {count} alerts")
            
            elif entity_type == "ips":
                count = db.query(Alert).filter(Alert.entity_ip == entity_value).count()
                if count >= ENTITY_FREQUENCY_THRESHOLD:
                    score += 8
                    reasons.append(f"IP '{entity_value}' in {count} alerts")
            
            elif entity_type == "devices":
                count = db.query(Alert).filter(Alert.entity_device == entity_value).count()
                if count >= ENTITY_FREQUENCY_THRESHOLD:
                    score += 5
                    reasons.append(f"Device '{entity_value}' in {count} alerts")
    
    reason = "; ".join(reasons) if reasons else "No frequent entities"
    return min(score, 30), reason  # Cap at 30


def detect_risk_indicators(
    alerts: List[Alert],
    entities: Dict[str, Set[str]],
    db: Session
) -> Tuple[float, List[str]]:
    """
    Detect risk patterns that indicate higher priority.
    
    Indicators:
    - Impossible travel (same user, different locations, short time)
    - Multiple users from same IP
    - Repeated failed actions
    - Off-hours activity
    - Known bad categories
    """
    score = 0
    reasons = []
    
    # Check for multiple users on same IP
    for ip in entities.get("ips", []):
        if not ip:
            continue
        users_on_ip = db.query(Alert.entity_user).filter(
            Alert.entity_ip == ip,
            Alert.entity_user.isnot(None)
        ).distinct().all()
        
        if len(users_on_ip) > 2:
            score += 15
            reasons.append(f"IP {ip} used by {len(users_on_ip)} different users")
    
    # Check for suspicious categories
    suspicious_categories = ["malware", "ransomware", "phishing", "credential theft", 
                            "lateral movement", "data exfiltration", "privilege escalation"]
    for alert in alerts:
        if alert.category and alert.category.lower() in suspicious_categories:
            score += 10
            reasons.append(f"High-risk category: {alert.category}")
            break  # Only count once
    
    # Check for impossible travel (placeholder - would need geolocation in production)
    locations = list(entities.get("locations", []))
    if len(locations) > 1 and len(entities.get("users", [])) == 1:
        # Same user, multiple locations
        user = list(entities["users"])[0] if entities.get("users") else "Unknown"
        
        # Check time span
        timestamps = [a.timestamp for a in alerts if a.timestamp]
        if timestamps:
            time_span = (max(timestamps) - min(timestamps)).total_seconds() / 3600
            if time_span < 2 and len(locations) > 1:
                score += 20
                reasons.append(f"Possible impossible travel: user {user} in {locations} within {time_span:.1f}h")
    
    # Check for multiple failed sign-ins
    failed_keywords = ["failed", "blocked", "denied", "unauthorized"]
    failed_count = sum(
        1 for a in alerts 
        if a.title and any(kw in a.title.lower() for kw in failed_keywords)
    )
    if failed_count >= 3:
        score += 10
        reasons.append(f"{failed_count} failed/blocked actions detected")
    
    # Check for off-hours activity (outside 6 AM - 8 PM)
    off_hours_count = sum(
        1 for a in alerts 
        if a.timestamp and (a.timestamp.hour < 6 or a.timestamp.hour > 20)
    )
    if off_hours_count > len(alerts) / 2:
        score += 5
        reasons.append(f"{off_hours_count}/{len(alerts)} alerts during off-hours")
    
    return min(score, 30), reasons  # Cap at 30


def calculate_triage_score(
    alerts: List[Alert],
    entities: Dict[str, Set[str]],
    db: Session
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate overall triage score with full explanation.
    
    Returns:
        Tuple of (total_score, explanation_dict)
    """
    severity_score, severity_reason = calculate_severity_score(alerts)
    entity_score, entity_reason = calculate_entity_frequency_score(alerts, entities, db)
    risk_score, risk_reasons = detect_risk_indicators(alerts, entities, db)
    
    total_score = severity_score + entity_score + risk_score
    
    explanation = {
        "severity_score": severity_score,
        "severity_reason": severity_reason,
        "entity_frequency_score": entity_score,
        "entity_reason": entity_reason,
        "risk_indicator_score": risk_score,
        "risk_reasons": risk_reasons,
        "total_score": total_score,
        "alert_count": len(alerts),
    }
    
    return total_score, explanation
