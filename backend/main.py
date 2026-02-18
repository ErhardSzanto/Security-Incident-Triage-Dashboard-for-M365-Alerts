"""
Security Incident Triage Dashboard - FastAPI Backend

Main application with REST API for:
- Alert ingestion and normalization
- Incident correlation and triage
- Analyst workflow management
- Report generation
"""
import json
import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from database import engine, get_db, Base
from models import Alert, Incident, AuditLog, IncidentStatus, Severity
from schemas import (
    AlertResponse, IncidentResponse, IncidentListResponse, IncidentUpdate,
    DashboardStats, UploadResponse, AuditLogResponse
)
from normalizer import parse_file_content
from correlator import correlate_alerts, recorrelate_all

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Security Incident Triage Dashboard",
    description="API for M365 security alert ingestion, correlation, and triage",
    version="1.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Audit Logging Helper ---
def log_action(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict = None,
    request: Request = None
):
    """Log an action to the audit trail."""
    audit = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        details=json.dumps(details) if details else None,
        ip_address=request.client.host if request else None
    )
    db.add(audit)
    db.commit()


# --- Dashboard Endpoints ---
@app.get("/api/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    total_alerts = db.query(Alert).count()
    total_incidents = db.query(Incident).count()
    
    # Count incidents by status
    new_incidents = db.query(Incident).filter(Incident.status == IncidentStatus.NEW).count()
    investigating = db.query(Incident).filter(Incident.status == IncidentStatus.INVESTIGATING).count()
    contained = db.query(Incident).filter(Incident.status == IncidentStatus.CONTAINED).count()
    closed = db.query(Incident).filter(Incident.status == IncidentStatus.CLOSED).count()
    
    # Critical = incidents with priority_score >= 70
    critical = db.query(Incident).filter(Incident.priority_score >= 70).count()
    
    return DashboardStats(
        total_alerts=total_alerts,
        total_incidents=total_incidents,
        critical_incidents=critical,
        new_incidents=new_incidents,
        investigating_incidents=investigating,
        contained_incidents=contained,
        closed_incidents=closed
    )


# --- Alert Endpoints ---
@app.get("/api/alerts", response_model=List[AlertResponse])
def get_alerts(
    skip: int = 0,
    limit: int = 100,
    severity: Optional[str] = None,
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all alerts with optional filtering."""
    query = db.query(Alert)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    if source:
        query = query.filter(Alert.source.ilike(f"%{source}%"))
    
    return query.order_by(Alert.timestamp.desc()).offset(skip).limit(limit).all()


@app.get("/api/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Get a specific alert by ID."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


# --- Incident Endpoints ---
@app.get("/api/incidents", response_model=List[IncidentListResponse])
def get_incidents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    min_priority: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Get all incidents with optional filtering."""
    query = db.query(Incident)
    
    if status:
        query = query.filter(Incident.status == status)
    if min_priority is not None:
        query = query.filter(Incident.priority_score >= min_priority)
    
    incidents = query.order_by(Incident.priority_score.desc()).offset(skip).limit(limit).all()
    
    return [
        IncidentListResponse(
            id=inc.id,
            title=inc.title,
            status=inc.status,
            priority_score=inc.priority_score,
            alert_count=len(inc.alerts),
            created_at=inc.created_at,
            updated_at=inc.updated_at
        )
        for inc in incidents
    ]


@app.get("/api/incidents/high-priority", response_model=List[IncidentListResponse])
def get_high_priority_incidents(limit: int = 10, db: Session = Depends(get_db)):
    """Get top high-priority incidents for the dashboard queue."""
    incidents = db.query(Incident).filter(
        Incident.status.in_([IncidentStatus.NEW, IncidentStatus.INVESTIGATING])
    ).order_by(Incident.priority_score.desc()).limit(limit).all()
    
    return [
        IncidentListResponse(
            id=inc.id,
            title=inc.title,
            status=inc.status,
            priority_score=inc.priority_score,
            alert_count=len(inc.alerts),
            created_at=inc.created_at,
            updated_at=inc.updated_at
        )
        for inc in incidents
    ]


@app.get("/api/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Get detailed incident information including all alerts."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.patch("/api/incidents/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: int,
    update: IncidentUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update incident status, notes, or evidence."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    changes = {}
    if update.status is not None:
        changes["status"] = {"old": incident.status.value, "new": update.status.value}
        incident.status = update.status
    if update.notes is not None:
        incident.notes = update.notes
        changes["notes"] = "updated"
    if update.evidence is not None:
        incident.evidence = update.evidence
        changes["evidence"] = "updated"
    
    incident.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(incident)
    
    # Audit log
    log_action(db, "status_change", "incident", incident_id, changes, request)
    
    return incident


# --- Data Ingestion Endpoints ---
@app.post("/api/upload", response_model=UploadResponse)
async def upload_alerts(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Upload JSON or CSV file containing security alerts."""
    # Validate file type
    if not file.filename.endswith(('.json', '.csv')):
        raise HTTPException(status_code=400, detail="Only JSON and CSV files are supported")
    
    # Read and parse file
    content = await file.read()
    try:
        content_str = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Use UTF-8.")
    
    try:
        normalized_alerts = parse_file_content(content_str, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
    
    if not normalized_alerts:
        raise HTTPException(status_code=400, detail="No valid alerts found in file")
    
    # Create alert records
    new_alerts = []
    skipped = 0
    for alert_data in normalized_alerts:
        # Check for duplicate alert_id
        existing = db.query(Alert).filter(Alert.alert_id == alert_data["alert_id"]).first()
        if existing:
            skipped += 1
            continue
        
        alert = Alert(**alert_data)
        db.add(alert)
        new_alerts.append(alert)
    
    db.commit()
    
    # Refresh to get IDs
    for alert in new_alerts:
        db.refresh(alert)
    
    # Run correlation
    incidents = correlate_alerts(db, new_alerts)
    db.commit()
    
    # Audit log
    log_action(db, "data_import", "alert", file.filename, {
        "alerts_imported": len(new_alerts),
        "skipped": skipped,
        "incidents_created": len(incidents)
    }, request)
    
    return UploadResponse(
        success=True,
        alerts_imported=len(new_alerts),
        incidents_created=len(incidents),
        message=f"Imported {len(new_alerts)} alerts, created {len(incidents)} incidents" + 
                (f" (skipped {skipped} duplicates)" if skipped else "")
    )


@app.post("/api/seed", response_model=UploadResponse)
def seed_demo_data(request: Request, db: Session = Depends(get_db)):
    """Load demo dataset for testing."""
    # Check for demo data files
    demo_dir = os.path.join(os.path.dirname(__file__), "..", "demo-data")
    
    if not os.path.exists(demo_dir):
        raise HTTPException(status_code=404, detail="Demo data directory not found")
    
    total_alerts = 0
    total_incidents = 0
    
    # Process all JSON and CSV files in demo-data
    for filename in os.listdir(demo_dir):
        if filename.endswith(('.json', '.csv')):
            filepath = os.path.join(demo_dir, filename)
            with open(filepath, 'r') as f:
                content = f.read()
            
            normalized_alerts = parse_file_content(content, filename)
            
            new_alerts = []
            for alert_data in normalized_alerts:
                existing = db.query(Alert).filter(Alert.alert_id == alert_data["alert_id"]).first()
                if existing:
                    continue
                
                alert = Alert(**alert_data)
                db.add(alert)
                new_alerts.append(alert)
            
            db.commit()
            
            for alert in new_alerts:
                db.refresh(alert)
            
            incidents = correlate_alerts(db, new_alerts)
            db.commit()
            
            total_alerts += len(new_alerts)
            total_incidents += len(incidents)
    
    # Audit log
    log_action(db, "data_import", "demo", "seed", {
        "alerts_imported": total_alerts,
        "incidents_created": total_incidents
    }, request)
    
    return UploadResponse(
        success=True,
        alerts_imported=total_alerts,
        incidents_created=total_incidents,
        message=f"Loaded demo data: {total_alerts} alerts, {total_incidents} incidents"
    )


@app.post("/api/recorrelate", response_model=UploadResponse)
def recorrelate_alerts(request: Request, db: Session = Depends(get_db)):
    """Re-run correlation on all existing alerts."""
    incidents = recorrelate_all(db)
    db.commit()
    
    total_alerts = db.query(Alert).count()
    
    log_action(db, "recorrelate", "system", "all", {
        "incidents_created": len(incidents)
    }, request)
    
    return UploadResponse(
        success=True,
        alerts_imported=total_alerts,
        incidents_created=len(incidents),
        message=f"Re-correlated {total_alerts} alerts into {len(incidents)} incidents"
    )


# --- Report Generation ---
@app.get("/api/incidents/{incident_id}/report", response_class=PlainTextResponse)
def generate_incident_report(incident_id: int, request: Request, db: Session = Depends(get_db)):
    """Generate incident report as Markdown."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Parse JSON fields
    users = json.loads(incident.related_users) if incident.related_users else []
    ips = json.loads(incident.related_ips) if incident.related_ips else []
    devices = json.loads(incident.related_devices) if incident.related_devices else []
    locations = json.loads(incident.related_locations) if incident.related_locations else []
    score_explanation = json.loads(incident.score_explanation) if incident.score_explanation else {}
    
    # Build report
    report = f"""# Incident Report: {incident.title}

## Summary
- **Incident ID**: {incident.id}
- **Status**: {incident.status.value.title()}
- **Priority Score**: {incident.priority_score:.1f}/100
- **Created**: {incident.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Last Updated**: {incident.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Total Alerts**: {len(incident.alerts)}

## Priority Score Breakdown
- **Severity Score**: {score_explanation.get('severity_score', 0)} - {score_explanation.get('severity_reason', 'N/A')}
- **Entity Frequency Score**: {score_explanation.get('entity_frequency_score', 0)} - {score_explanation.get('entity_reason', 'N/A')}
- **Risk Indicator Score**: {score_explanation.get('risk_indicator_score', 0)}
"""
    
    risk_reasons = score_explanation.get('risk_reasons', [])
    if risk_reasons:
        for reason in risk_reasons:
            report += f"  - {reason}\n"
    
    report += f"""
## Related Entities
### Users ({len(users)})
"""
    for user in users:
        report += f"- {user}\n"
    
    report += f"""
### IP Addresses ({len(ips)})
"""
    for ip in ips:
        report += f"- {ip}\n"
    
    report += f"""
### Devices ({len(devices)})
"""
    for device in devices:
        report += f"- {device}\n"
    
    report += f"""
### Locations ({len(locations)})
"""
    for loc in locations:
        report += f"- {loc}\n"
    
    report += """
## Alert Timeline
"""
    for alert in sorted(incident.alerts, key=lambda a: a.timestamp or datetime.min):
        ts = alert.timestamp.strftime('%Y-%m-%d %H:%M:%S') if alert.timestamp else 'Unknown'
        report += f"### {ts} - {alert.title}\n"
        report += f"- **Source**: {alert.source}\n"
        report += f"- **Category**: {alert.category}\n"
        report += f"- **Severity**: {alert.severity.value.title()}\n"
        if alert.description:
            report += f"- **Description**: {alert.description}\n"
        report += "\n"
    
    if incident.notes:
        report += f"""## Analyst Notes
{incident.notes}
"""
    
    if incident.evidence:
        report += f"""
## Evidence
{incident.evidence}
"""
    
    report += f"""
---
*Report generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
    
    # Audit log
    log_action(db, "report_export", "incident", incident_id, {"format": "markdown"}, request)
    
    return report


# --- Audit Log Endpoints ---
@app.get("/api/audit-log", response_model=List[AuditLogResponse])
def get_audit_log(
    skip: int = 0,
    limit: int = 100,
    action: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get audit log entries."""
    query = db.query(AuditLog)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()


# --- Health Check ---
@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
