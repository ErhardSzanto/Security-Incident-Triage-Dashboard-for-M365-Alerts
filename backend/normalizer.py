"""
Alert normalizer - converts various M365/security alert formats to unified schema.

Supported formats:
- Microsoft Defender alerts
- Azure AD sign-in alerts  
- M365 compliance alerts
- Generic JSON/CSV with field mapping
"""
import json
import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from models import Severity


# Severity mapping from various source formats
SEVERITY_MAPPINGS = {
    # Microsoft Defender
    "informational": Severity.LOW,
    "low": Severity.LOW,
    "medium": Severity.MEDIUM,
    "high": Severity.HIGH,
    "critical": Severity.CRITICAL,
    # Numeric mappings
    "1": Severity.LOW,
    "2": Severity.MEDIUM,
    "3": Severity.HIGH,
    "4": Severity.CRITICAL,
    # Risk levels
    "none": Severity.LOW,
    "hidden": Severity.LOW,
    "elevated": Severity.MEDIUM,
    "significant": Severity.HIGH,
    "severe": Severity.CRITICAL,
}


# Field mappings for different alert sources
FIELD_MAPPINGS = {
    "defender": {
        "alert_id": ["alertId", "id", "AlertId"],
        "title": ["title", "alertTitle", "Title"],
        "description": ["description", "alertDescription", "Description"],
        "severity": ["severity", "alertSeverity", "Severity"],
        "category": ["category", "alertCategory", "Category"],
        "timestamp": ["createdDateTime", "timestamp", "detectionTime", "CreatedDateTime"],
        "entity_user": ["userPrincipalName", "accountName", "user", "User", "userEmail"],
        "entity_ip": ["ipAddress", "sourceIp", "clientIp", "IpAddress"],
        "entity_device": ["deviceName", "machineName", "computerName", "DeviceName"],
        "entity_location": ["location", "country", "city", "Location"],
    },
    "azure_ad": {
        "alert_id": ["id", "correlationId"],
        "title": ["riskEventType", "riskType"],
        "description": ["additionalInfo", "riskDetail"],
        "severity": ["riskLevel", "riskState"],
        "category": ["riskEventType", "detectionTimingType"],
        "timestamp": ["activityDateTime", "detectedDateTime"],
        "entity_user": ["userPrincipalName", "userDisplayName"],
        "entity_ip": ["ipAddress"],
        "entity_device": ["deviceDetail.displayName", "deviceDetail.deviceId"],
        "entity_location": ["location.city", "location.countryOrRegion"],
    },
    "generic": {
        "alert_id": ["id", "alert_id", "alertId", "ID"],
        "title": ["title", "name", "alert_name", "Title"],
        "description": ["description", "details", "message", "Description"],
        "severity": ["severity", "priority", "risk_level", "Severity"],
        "category": ["category", "type", "alert_type", "Category"],
        "timestamp": ["timestamp", "time", "date", "created_at", "Timestamp"],
        "entity_user": ["user", "username", "user_email", "account", "User"],
        "entity_ip": ["ip", "ip_address", "source_ip", "client_ip", "IP"],
        "entity_device": ["device", "machine", "hostname", "computer", "Device"],
        "entity_location": ["location", "country", "region", "Location"],
    }
}


def get_nested_value(obj: Dict, key_path: str) -> Optional[Any]:
    """Get value from nested dict using dot notation (e.g., 'location.city')."""
    keys = key_path.split(".")
    value = obj
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value


def find_field_value(alert_data: Dict, field_options: List[str]) -> Optional[str]:
    """Try multiple field names to find a value in the alert data."""
    for field in field_options:
        value = get_nested_value(alert_data, field)
        if value is not None:
            return str(value) if value else None
    return None


def normalize_severity(severity_value: Optional[str]) -> Severity:
    """Convert various severity formats to standard enum."""
    if not severity_value:
        return Severity.MEDIUM
    
    normalized = severity_value.lower().strip()
    return SEVERITY_MAPPINGS.get(normalized, Severity.MEDIUM)


def parse_timestamp(timestamp_value: Optional[str]) -> datetime:
    """Parse various timestamp formats to datetime."""
    if not timestamp_value:
        return datetime.utcnow()
    
    # Common ISO formats
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_value, fmt)
        except ValueError:
            continue
    
    return datetime.utcnow()


def detect_source(alert_data: Dict) -> str:
    """Detect the source format of an alert based on field presence."""
    # Check for Microsoft Defender specific fields
    if "alertId" in alert_data or "detectionSource" in alert_data:
        return "defender"
    
    # Check for Azure AD specific fields
    if "riskEventType" in alert_data or "riskLevel" in alert_data:
        return "azure_ad"
    
    # Check for source field
    source = alert_data.get("source", "").lower()
    if "defender" in source:
        return "defender"
    if "azure" in source or "aad" in source:
        return "azure_ad"
    
    return "generic"


def normalize_alert(alert_data: Dict, source_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Normalize a single alert from any supported format to unified schema.
    
    Returns dict with: alert_id, source, category, severity, title, description,
                       entity_user, entity_ip, entity_device, entity_location, timestamp
    """
    source_type = source_hint or detect_source(alert_data)
    mapping = FIELD_MAPPINGS.get(source_type, FIELD_MAPPINGS["generic"])
    
    # Extract values using field mapping
    alert_id = find_field_value(alert_data, mapping["alert_id"])
    if not alert_id:
        # Generate ID if not found
        alert_id = f"auto-{hash(json.dumps(alert_data, sort_keys=True, default=str)) % 10**8}"
    
    title = find_field_value(alert_data, mapping["title"]) or "Unknown Alert"
    description = find_field_value(alert_data, mapping["description"])
    severity_raw = find_field_value(alert_data, mapping["severity"])
    category = find_field_value(alert_data, mapping["category"]) or "Unknown"
    timestamp_raw = find_field_value(alert_data, mapping["timestamp"])
    
    # Determine source name
    source_name = alert_data.get("source", source_type.replace("_", " ").title())
    
    return {
        "alert_id": alert_id,
        "source": source_name,
        "category": category,
        "severity": normalize_severity(severity_raw),
        "title": title,
        "description": description,
        "entity_user": find_field_value(alert_data, mapping["entity_user"]),
        "entity_ip": find_field_value(alert_data, mapping["entity_ip"]),
        "entity_device": find_field_value(alert_data, mapping["entity_device"]),
        "entity_location": find_field_value(alert_data, mapping["entity_location"]),
        "timestamp": parse_timestamp(timestamp_raw),
        "raw_data": json.dumps(alert_data, default=str),
    }


def parse_json_file(content: str) -> List[Dict[str, Any]]:
    """Parse JSON content (single alert or array of alerts)."""
    data = json.loads(content)
    
    # Handle array of alerts
    if isinstance(data, list):
        return [normalize_alert(alert) for alert in data]
    
    # Handle single alert
    if isinstance(data, dict):
        # Check if alerts are nested under a key
        if "value" in data:  # Microsoft Graph API format
            return [normalize_alert(alert) for alert in data["value"]]
        if "alerts" in data:
            return [normalize_alert(alert) for alert in data["alerts"]]
        # Single alert
        return [normalize_alert(data)]
    
    return []


def parse_csv_file(content: str) -> List[Dict[str, Any]]:
    """Parse CSV content to alerts."""
    reader = csv.DictReader(io.StringIO(content))
    return [normalize_alert(dict(row)) for row in reader]


def parse_file_content(content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse file content based on extension."""
    if filename.lower().endswith(".csv"):
        return parse_csv_file(content)
    else:
        return parse_json_file(content)
