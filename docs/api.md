# API Documentation

Base URL: `http://localhost:8000/api`

## Dashboard

### Get Statistics

```
GET /stats
```

Returns dashboard statistics.

**Response:**
```json
{
  "total_alerts": 20,
  "total_incidents": 5,
  "critical_incidents": 2,
  "new_incidents": 3,
  "investigating_incidents": 1,
  "contained_incidents": 1,
  "closed_incidents": 0
}
```

---

## Alerts

### List Alerts

```
GET /alerts
```

**Query Parameters:**
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Page size (default: 100)
- `severity` (string): Filter by severity (low, medium, high, critical)
- `source` (string): Filter by source (partial match)

**Response:**
```json
[
  {
    "id": 1,
    "alert_id": "def-001",
    "source": "Microsoft Defender",
    "category": "Suspicious Sign-in",
    "severity": "high",
    "title": "Suspicious sign-in from unfamiliar location",
    "description": "User signed in from...",
    "entity_user": "john.doe@contoso.com",
    "entity_ip": "185.220.101.45",
    "entity_device": "LAPTOP-JD001",
    "entity_location": "Moscow, Russia",
    "timestamp": "2024-01-15T03:22:00Z",
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

### Get Alert

```
GET /alerts/{alert_id}
```

**Response:** Single alert object (same schema as list item)

---

## Incidents

### List Incidents

```
GET /incidents
```

**Query Parameters:**
- `skip` (int): Pagination offset
- `limit` (int): Page size
- `status` (string): Filter by status (new, investigating, contained, closed)
- `min_priority` (float): Minimum priority score

**Response:**
```json
[
  {
    "id": 1,
    "title": "Critical Phishing Incident (3 alerts)",
    "status": "new",
    "priority_score": 75.0,
    "alert_count": 3,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
]
```

### Get High Priority Incidents

```
GET /incidents/high-priority
```

Returns incidents with status `new` or `investigating`, sorted by priority.

**Query Parameters:**
- `limit` (int): Maximum results (default: 10)

### Get Incident Details

```
GET /incidents/{incident_id}
```

**Response:**
```json
{
  "id": 1,
  "title": "Critical Phishing Incident",
  "status": "investigating",
  "priority_score": 75.0,
  "score_explanation": "{\"severity_score\": 40, ...}",
  "related_users": "[\"john.doe@contoso.com\"]",
  "related_ips": "[\"185.220.101.45\"]",
  "related_devices": "[\"LAPTOP-JD001\"]",
  "related_locations": "[\"Moscow, Russia\"]",
  "notes": "Analyst notes...",
  "evidence": "Evidence text...",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T11:30:00Z",
  "alerts": [...]
}
```

### Update Incident

```
PATCH /incidents/{incident_id}
```

**Request Body:**
```json
{
  "status": "investigating",
  "notes": "Updated investigation notes",
  "evidence": "New evidence"
}
```

All fields are optional.

**Response:** Updated incident object

### Generate Report

```
GET /incidents/{incident_id}/report
```

**Response:** Markdown report (Content-Type: text/plain)

---

## Data Ingestion

### Upload Alert File

```
POST /upload
```

**Request:** multipart/form-data with `file` field

**Supported Formats:** JSON, CSV

**Response:**
```json
{
  "success": true,
  "alerts_imported": 10,
  "incidents_created": 3,
  "message": "Imported 10 alerts, created 3 incidents"
}
```

### Load Demo Data

```
POST /seed
```

Loads sample data from `/demo-data` directory.

**Response:**
```json
{
  "success": true,
  "alerts_imported": 20,
  "incidents_created": 5,
  "message": "Loaded demo data: 20 alerts, 5 incidents"
}
```

### Re-correlate Alerts

```
POST /recorrelate
```

Re-runs correlation algorithm on all existing alerts.

---

## Audit Log

### Get Audit Log

```
GET /audit-log
```

**Query Parameters:**
- `skip` (int): Pagination offset
- `limit` (int): Page size
- `action` (string): Filter by action type

**Response:**
```json
[
  {
    "id": 1,
    "action": "data_import",
    "entity_type": "alert",
    "entity_id": "defender-alerts.json",
    "details": "{\"alerts_imported\": 10}",
    "user": "analyst",
    "timestamp": "2024-01-15T10:00:00Z"
  }
]
```

---

## Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message describing the issue"
}
```

**Status Codes:**
- `400`: Bad request (invalid input)
- `404`: Resource not found
- `500`: Server error
