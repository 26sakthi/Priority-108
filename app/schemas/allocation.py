from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

class AmbulanceType(str, Enum):
    ALS = "ALS"  # Advanced Life Support (Paramedic, Ventilator, Defib)
    BLS = "BLS"  # Basic Life Support (EMT, First Aid, AED, Oxygen)

class AmbulanceStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    OFFLINE = "OFFLINE"

class AssignmentStatus(str, Enum):
    ASSIGNED = "ASSIGNED"
    QUEUED_AWAITING_UNIT = "QUEUED_AWAITING_UNIT"
    CANCELLED = "CANCELLED"

class PriorityTier(str, Enum):
    P1_CRITICAL = "P1_CRITICAL"
    P2_HIGH_URGENCY = "P2_HIGH_URGENCY"
    P3_LOWER_URGENCY = "P3_LOWER_URGENCY"

# --- Request Schemas ---

class AllocationRequest(BaseModel):
    incident_id: UUID = Field(..., description="Unique emergency incident identifier")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Patient WGS 84 latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Patient WGS 84 longitude")
    required_capability: AmbulanceType = Field(
        default=AmbulanceType.BLS,
        description="Required capability (derived from clinical triage: ALS for P1 cardiac/trauma, BLS for P2/P3)"
    )
    priority_tier: PriorityTier = Field(
        default=PriorityTier.P2_HIGH_URGENCY,
        description="Clinical urgency classification"
    )
    max_acceptable_est_seconds: Optional[int] = Field(
        default=1800,
        ge=60,
        le=7200,
        description="Cut-off travel time threshold in seconds (default: 1800s / 30m)"
    )

class AmbulanceCreate(BaseModel):
    vehicle_code: str = Field(..., min_length=2, max_length=30)
    ambulance_type: AmbulanceType
    status: AmbulanceStatus = AmbulanceStatus.AVAILABLE
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

# --- Response Schemas ---

class AllocationData(BaseModel):
    assignment_id: UUID
    incident_id: UUID
    assigned_ambulance_id: Optional[UUID] = None
    vehicle_code: Optional[str] = None
    ambulance_type: Optional[AmbulanceType] = None
    est_travel_seconds: Optional[int] = None
    distance_meters: Optional[int] = None
    assignment_status: AssignmentStatus
    allocation_rationale: str
    is_capability_downgrade: bool = False
    assigned_at: datetime

class AllocationResponse(BaseModel):
    success: bool = True
    data: AllocationData
    message: str

class AmbulanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ambulance_id: UUID
    vehicle_code: str
    ambulance_type: AmbulanceType
    status: AmbulanceStatus
    latitude: float
    longitude: float
    last_location_update: datetime

class StandardErrorResponse(BaseModel):
    success: bool = False
    error: dict
