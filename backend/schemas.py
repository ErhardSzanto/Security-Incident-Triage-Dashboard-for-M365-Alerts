"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from models import Severity, IncidentStatus


# Alert Schemas
class AlertBase(BaseModel):
    alert_id: str
    source: str
    category: str
    severity: Severity
    title: str
    description: Optional[str] = None
    entity_user: Optional[str] = None
    entity_ip: Optional[str] = None
    entity_device: Optional[str] = None
    entity_location: Optional[str] = None
    timestamp: Optional[datetime] = None


class AlertCreate(AlertBase):
    raw_data: Optional[str] = None


class AlertResponse(AlertBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Incident Schemas
class IncidentBase(BaseModel):
    title: str
    status: IncidentStatus = IncidentStatus.NEW
    notes: Optional[str] = None
    evidence: Optional[str] = None


class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    notes: Optional[str] = None
    evidence: Optional[str] = None


class ScoreExplanation(BaseModel):
    severity_score: float
    severity_reason: str
    entity_frequency_score: float
    entity_reason: str
    risk_indicator_score: float
    risk_reasons: List[str]
    total_score: float


class IncidentResponse(IncidentBase):
    id: int
    priority_score: float
    score_explanation: Optional[str] = None
    related_users: Optional[str] = None
    related_ips: Optional[str] = None
    related_devices: Optional[str] = None
    related_locations: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    alerts: List[AlertResponse] = []

    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    id: int
    title: str
    status: IncidentStatus
    priority_score: float
    alert_count: int
    created_at: datetime
    updated_at: datetime


# Dashboard Stats
class DashboardStats(BaseModel):
    total_alerts: int
    total_incidents: int
    critical_incidents: int
    new_incidents: int
    investigating_incidents: int
    contained_incidents: int
    closed_incidents: int


# Upload Response
class UploadResponse(BaseModel):
    success: bool
    alerts_imported: int
    incidents_created: int
    message: str


# Audit Log
class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: str
    details: Optional[str] = None
    user: str
    timestamp: datetime

    class Config:
        from_attributes = True
