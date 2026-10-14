import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class DispatchAssignment(Base):
    __tablename__ = "dispatch_assignments_v2"

    assignment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    ambulance_id = Column(UUID(as_uuid=True), ForeignKey("ambulances_v2.ambulance_id", ondelete="SET NULL"), nullable=True, index=True)
    assignment_status = Column(String(30), nullable=False)  # 'ASSIGNED', 'QUEUED_AWAITING_UNIT', 'CANCELLED'
    est_travel_seconds = Column(Integer, nullable=True)
    distance_meters = Column(Integer, nullable=True)
    allocation_rationale = Column(String(500), nullable=False)
    is_capability_downgrade = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_active_incident_assignment", "incident_id", unique=True, postgresql_where=(is_active == True)),
    )

    def __repr__(self):
        return f"<DispatchAssignment {self.assignment_id} -> Incident {self.incident_id} | Unit {self.ambulance_id}>"
