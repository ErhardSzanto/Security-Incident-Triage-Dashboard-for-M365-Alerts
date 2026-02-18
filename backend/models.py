"""SQLAlchemy ORM models for alerts, incidents, and audit logging."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from database import Base


class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, enum.Enum):
    NEW = "new"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    CLOSED = "closed"


# Association table for many-to-many relationship between alerts and incidents
incident_alerts = Table(
    "incident_alerts",
    Base.metadata,
    Column("incident_id", Integer, ForeignKey("incidents.id"), primary_key=True),
    Column("alert_id", Integer, ForeignKey("alerts.id"), primary_key=True),
)


class Alert(Base):
    """Normalized security alert from various sources."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(255), unique=True, index=True)  # Original alert ID from source
    source = Column(String(100))  # e.g., "Microsoft Defender", "Azure AD", "M365"
    category = Column(String(100))  # e.g., "Malware", "Phishing", "Suspicious Sign-in"
    severity = Column(SQLEnum(Severity), default=Severity.MEDIUM)
    title = Column(String(500))
    description = Column(Text)
    
    # Entity fields for correlation
    entity_user = Column(String(255), index=True)
    entity_ip = Column(String(45), index=True)  # Supports IPv6
    entity_device = Column(String(255), index=True)
    entity_location = Column(String(255))
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    raw_data = Column(Text)  # Original JSON for reference
    created_at = Column(DateTime, default=datetime.utcnow)

    incidents = relationship("Incident", secondary=incident_alerts, back_populates="alerts")


class Incident(Base):
    """Correlated group of related alerts forming a security incident."""
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500))
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.NEW)
    priority_score = Column(Float, default=0.0)
    score_explanation = Column(Text)  # JSON explaining score factors
    
    # Aggregated entities from all alerts
    related_users = Column(Text)  # JSON array
    related_ips = Column(Text)  # JSON array
    related_devices = Column(Text)  # JSON array
    related_locations = Column(Text)  # JSON array
    
    notes = Column(Text)
    evidence = Column(Text)  # Analyst-attached evidence (text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    alerts = relationship("Alert", secondary=incident_alerts, back_populates="incidents")


class AuditLog(Base):
    """Audit trail for key system actions."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100))  # e.g., "login", "data_import", "status_change", "report_export"
    entity_type = Column(String(50))  # e.g., "incident", "alert", "user"
    entity_id = Column(String(100))
    details = Column(Text)  # JSON with action details
    user = Column(String(255), default="analyst")  # Would be real user in production
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.utcnow)
