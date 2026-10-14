import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Ambulance(Base):
    __tablename__ = "ambulances_v2"

    ambulance_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_code = Column(String(30), unique=True, nullable=False, index=True)
    ambulance_type = Column(String(10), nullable=False)  # 'ALS', 'BLS'
    status = Column(String(20), nullable=False, default="AVAILABLE", index=True)  # 'AVAILABLE', 'ASSIGNED', 'OFFLINE'
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    last_location_update = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Ambulance {self.vehicle_code} [{self.ambulance_type}] - {self.status}>"
