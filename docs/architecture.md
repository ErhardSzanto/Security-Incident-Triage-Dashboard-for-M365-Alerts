# Architecture Overview

## System Components

### Frontend (React + TypeScript)

```
┌─────────────────────────────────────────────┐
│                  App.tsx                     │
│  ┌─────────────────────────────────────┐    │
│  │           React Router               │    │
│  │  /           → Dashboard             │    │
│  │  /incidents  → IncidentList          │    │
│  │  /incidents/:id → IncidentDetail     │    │
│  │  /alerts     → AlertList             │    │
│  │  /upload     → DataUpload            │    │
│  └─────────────────────────────────────┘    │
│                    │                         │
│                    ▼                         │
│  ┌─────────────────────────────────────┐    │
│  │            api.ts                    │    │
│  │   Typed API client for backend       │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### Backend (FastAPI + SQLAlchemy)

```
┌─────────────────────────────────────────────────────┐
│                    main.py                           │
│  ┌────────────────────────────────────────────┐     │
│  │              API Routes                     │     │
│  │  GET  /api/stats                           │     │
│  │  GET  /api/alerts, /api/alerts/{id}        │     │
│  │  GET  /api/incidents, /api/incidents/{id}  │     │
│  │  PATCH /api/incidents/{id}                 │     │
│  │  GET  /api/incidents/{id}/report           │     │
│  │  POST /api/upload, /api/seed               │     │
│  └────────────────────────────────────────────┘     │
│         │              │              │              │
│         ▼              ▼              ▼              │
│  ┌──────────┐  ┌────────────┐  ┌──────────────┐     │
│  │normalizer│  │ correlator │  │    triage    │     │
│  │          │  │            │  │              │     │
│  │ JSON/CSV │  │  Entity    │  │  Severity    │     │
│  │ parsing  │  │  matching  │  │  scoring     │     │
│  │ Field    │  │  Time      │  │  Risk        │     │
│  │ mapping  │  │  window    │  │  indicators  │     │
│  └──────────┘  └────────────┘  └──────────────┘     │
│         │              │              │              │
│         └──────────────┼──────────────┘              │
│                        ▼                             │
│  ┌────────────────────────────────────────────┐     │
│  │              models.py                      │     │
│  │   Alert | Incident | AuditLog              │     │
│  └────────────────────────────────────────────┘     │
│                        │                             │
│                        ▼                             │
│  ┌────────────────────────────────────────────┐     │
│  │              database.py                    │     │
│  │           SQLite + SQLAlchemy              │     │
│  └────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

## Data Flow

### Alert Ingestion

```
1. File Upload (JSON/CSV)
         │
         ▼
2. Parse & Validate
   normalizer.parse_file_content()
         │
         ▼
3. Normalize to Unified Schema
   normalizer.normalize_alert()
         │
         ▼
4. Store in Database
   models.Alert
         │
         ▼
5. Run Correlation
   correlator.correlate_alerts()
         │
         ▼
6. Calculate Triage Score
   triage.calculate_triage_score()
         │
         ▼
7. Create/Update Incident
   models.Incident
```

### Correlation Algorithm

```
For each new alert:
  1. Find related alerts within time window (±1 hour)
  2. Calculate entity overlap score:
     - User match: +2 points
     - IP match: +1 point
     - Device match: +1 point
  3. If overlap >= 1, group into same incident
  4. Check if related alerts already in an incident
  5. Create new incident or add to existing
```

### Triage Scoring

```
Total Score = Severity + Entity Frequency + Risk Indicators

Severity (10-40 points):
- Critical: 40
- High: 30
- Medium: 20
- Low: 10
- Bonus for multiple high/critical alerts

Entity Frequency (0-30 points):
- User appears in 3+ alerts: +10
- IP appears in 3+ alerts: +8
- Device appears in 3+ alerts: +5

Risk Indicators (0-30 points):
- Multiple users on same IP: +15
- High-risk category: +10
- Impossible travel: +20
- Multiple failed auth: +10
- Off-hours activity: +5
```

## Database Schema

```sql
-- Alerts table
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    alert_id VARCHAR(255) UNIQUE,
    source VARCHAR(100),
    category VARCHAR(100),
    severity ENUM('low', 'medium', 'high', 'critical'),
    title VARCHAR(500),
    description TEXT,
    entity_user VARCHAR(255),
    entity_ip VARCHAR(45),
    entity_device VARCHAR(255),
    entity_location VARCHAR(255),
    timestamp DATETIME,
    raw_data TEXT,
    created_at DATETIME
);

-- Incidents table
CREATE TABLE incidents (
    id INTEGER PRIMARY KEY,
    title VARCHAR(500),
    status ENUM('new', 'investigating', 'contained', 'closed'),
    priority_score FLOAT,
    score_explanation TEXT,  -- JSON
    related_users TEXT,      -- JSON array
    related_ips TEXT,        -- JSON array
    related_devices TEXT,    -- JSON array
    related_locations TEXT,  -- JSON array
    notes TEXT,
    evidence TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

-- Many-to-many relationship
CREATE TABLE incident_alerts (
    incident_id INTEGER,
    alert_id INTEGER,
    PRIMARY KEY (incident_id, alert_id),
    FOREIGN KEY (incident_id) REFERENCES incidents(id),
    FOREIGN KEY (alert_id) REFERENCES alerts(id)
);

-- Audit log
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    action VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id VARCHAR(100),
    details TEXT,  -- JSON
    user VARCHAR(255),
    ip_address VARCHAR(45),
    timestamp DATETIME
);
```

## Extensibility Points

1. **New Alert Sources**: Add mappings in `normalizer.py` FIELD_MAPPINGS
2. **Risk Indicators**: Add detection functions in `triage.py`
3. **Correlation Rules**: Modify `correlator.py` parameters
4. **Authentication**: Add middleware in `main.py`
5. **Database**: Replace SQLite connection in `database.py`
