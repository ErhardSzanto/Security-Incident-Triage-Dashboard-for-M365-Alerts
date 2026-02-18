"""
Correlation engine - groups related alerts into security incidents.

Correlation criteria:
- Entity overlap (same user, IP, device)
- Time window proximity (±1 hour by default)
- Category relationships
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from sqlalchemy.orm import Session
from models import Alert, Incident, IncidentStatus


# Time window for correlating alerts (in hours)
CORRELATION_TIME_WINDOW_HOURS = 1

# Minimum entity overlap score to correlate alerts
MIN_OVERLAP_SCORE = 1


def calculate_entity_overlap(alert1: Alert, alert2: Alert) -> int:
    """
    Calculate entity overlap score between two alerts.
    Returns number of matching entities.
    """
    score = 0
    
    if alert1.entity_user and alert2.entity_user:
        if alert1.entity_user.lower() == alert2.entity_user.lower():
            score += 2  # User match is weighted higher
    
    if alert1.entity_ip and alert2.entity_ip:
        if alert1.entity_ip == alert2.entity_ip:
            score += 1
    
    if alert1.entity_device and alert2.entity_device:
        if alert1.entity_device.lower() == alert2.entity_device.lower():
            score += 1
    
    return score


def is_within_time_window(alert1: Alert, alert2: Alert, hours: int = CORRELATION_TIME_WINDOW_HOURS) -> bool:
    """Check if two alerts are within the correlation time window."""
    if not alert1.timestamp or not alert2.timestamp:
        return True  # If no timestamp, assume within window
    
    time_diff = abs((alert1.timestamp - alert2.timestamp).total_seconds())
    return time_diff <= hours * 3600


def find_related_alerts(
    new_alert: Alert, 
    existing_alerts: List[Alert],
    time_window_hours: int = CORRELATION_TIME_WINDOW_HOURS
) -> List[Alert]:
    """Find all alerts that correlate with the given alert."""
    related = []
    
    for existing in existing_alerts:
        if existing.id == new_alert.id:
            continue
        
        # Check time window
        if not is_within_time_window(new_alert, existing, time_window_hours):
            continue
        
        # Check entity overlap
        overlap = calculate_entity_overlap(new_alert, existing)
        if overlap >= MIN_OVERLAP_SCORE:
            related.append(existing)
    
    return related


def collect_entities(alerts: List[Alert]) -> Dict[str, Set[str]]:
    """Collect all unique entities from a list of alerts."""
    entities = {
        "users": set(),
        "ips": set(),
        "devices": set(),
        "locations": set(),
    }
    
    for alert in alerts:
        if alert.entity_user:
            entities["users"].add(alert.entity_user)
        if alert.entity_ip:
            entities["ips"].add(alert.entity_ip)
        if alert.entity_device:
            entities["devices"].add(alert.entity_device)
        if alert.entity_location:
            entities["locations"].add(alert.entity_location)
    
    return entities


def generate_incident_title(alerts: List[Alert]) -> str:
    """Generate a descriptive title for an incident based on its alerts."""
    if not alerts:
        return "Unknown Incident"
    
    # Get unique categories
    categories = list(set(a.category for a in alerts if a.category))
    
    # Get highest severity
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    max_severity = max(alerts, key=lambda a: severity_order.get(a.severity.value, 0))
    
    # Build title
    if len(categories) == 1:
        return f"{max_severity.severity.value.title()} {categories[0]} Incident"
    elif len(categories) > 1:
        return f"{max_severity.severity.value.title()} Multi-Category Incident ({len(alerts)} alerts)"
    else:
        return f"{max_severity.severity.value.title()} Security Incident"


def create_or_update_incident(
    db: Session,
    alerts: List[Alert],
    existing_incident: Optional[Incident] = None
) -> Incident:
    """Create a new incident or update existing one with the given alerts."""
    from triage import calculate_triage_score  # Import here to avoid circular import
    
    entities = collect_entities(alerts)
    
    if existing_incident:
        incident = existing_incident
        # Merge alerts
        for alert in alerts:
            if alert not in incident.alerts:
                incident.alerts.append(alert)
        alerts = incident.alerts  # Recalculate with all alerts
        entities = collect_entities(alerts)
        incident.title = generate_incident_title(alerts)
    else:
        incident = Incident(
            title=generate_incident_title(alerts),
            status=IncidentStatus.NEW,
        )
        incident.alerts = alerts
    
    # Store entity lists as JSON
    incident.related_users = json.dumps(list(entities["users"]))
    incident.related_ips = json.dumps(list(entities["ips"]))
    incident.related_devices = json.dumps(list(entities["devices"]))
    incident.related_locations = json.dumps(list(entities["locations"]))
    
    # Calculate triage score
    score, explanation = calculate_triage_score(alerts, entities, db)
    incident.priority_score = score
    incident.score_explanation = json.dumps(explanation)
    
    if not existing_incident:
        db.add(incident)
    
    return incident


def correlate_alerts(db: Session, new_alerts: List[Alert]) -> List[Incident]:
    """
    Main correlation function. Takes new alerts and:
    1. Finds related existing alerts/incidents
    2. Groups new alerts with each other
    3. Creates or updates incidents
    
    Returns list of created/updated incidents.
    """
    if not new_alerts:
        return []
    
    # Get all existing alerts for correlation
    existing_alerts = db.query(Alert).all()
    
    # Track which alerts have been assigned to incidents
    assigned_alerts: Set[int] = set()
    incidents: List[Incident] = []
    
    for new_alert in new_alerts:
        if new_alert.id in assigned_alerts:
            continue
        
        # Find related alerts (both new and existing)
        all_alerts = existing_alerts + new_alerts
        related = find_related_alerts(new_alert, all_alerts)
        
        # Check if any related alerts are already in an incident
        existing_incident = None
        for related_alert in related:
            if related_alert.incidents:
                existing_incident = related_alert.incidents[0]
                break
        
        # Collect alert group
        alert_group = [new_alert] + [a for a in related if a in new_alerts and a.id not in assigned_alerts]
        
        # Create or update incident
        incident = create_or_update_incident(db, alert_group, existing_incident)
        incidents.append(incident)
        
        # Mark alerts as assigned
        for alert in alert_group:
            assigned_alerts.add(alert.id)
    
    return incidents


def recorrelate_all(db: Session) -> List[Incident]:
    """
    Re-run correlation on all alerts.
    Useful after importing new data or adjusting correlation parameters.
    """
    # Clear existing incident associations
    db.query(Incident).delete()
    db.commit()
    
    # Get all alerts
    all_alerts = db.query(Alert).order_by(Alert.timestamp).all()
    
    # Re-correlate
    return correlate_alerts(db, all_alerts)
