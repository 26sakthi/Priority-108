from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum

class IncidentStatus(str, Enum):
    REPORTED = "REPORTED"
    TRIAGED = "TRIAGED"
    DISPATCHING = "DISPATCHING"
    DISPATCHED = "DISPATCHED"
    ON_SCENE = "ON_SCENE"
    TRANSPORTING = "TRANSPORTING"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"

class PriorityTier(str, Enum):
    P1_CRITICAL = "P1_CRITICAL"
    P2_HIGH_URGENCY = "P2_HIGH_URGENCY"
    P3_LOWER_URGENCY = "P3_LOWER_URGENCY"

class AmbulanceType(str, Enum):
    ALS = "ALS"
    BLS = "BLS"
    PTS = "PTS"

class AmbulanceStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    EN_ROUTE_SCENE = "EN_ROUTE_SCENE"
    AT_SCENE = "AT_SCENE"
    EN_ROUTE_HOSPITAL = "EN_ROUTE_HOSPITAL"
    AT_HOSPITAL = "AT_HOSPITAL"
    MAINTENANCE = "MAINTENANCE"

class MatchConfidence(str, Enum):
    HIGH_MATCH = "HIGH_MATCH"
    UNCERTAIN_MATCH = "UNCERTAIN_MATCH"
    NO_MATCH = "NO_MATCH"

class FacilitySpecialty(str, Enum):
    TRAUMA_LEVEL_1 = "TRAUMA_LEVEL_1"
    CARDIAC_CATH_LAB = "CARDIAC_CATH_LAB"
    BURN_CARE = "BURN_CARE"
    NEUROLOGY = "NEUROLOGY"
    PEDIATRIC_ICU = "PEDIATRIC_ICU"
    GENERAL_EMERGENCY = "GENERAL_EMERGENCY"

class GeoLocation(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

class QuestionOption(BaseModel):
    value: str
    label: str
    urgency_weight: int = 0
    trigger_instant_p1: bool = False

class QuestionSchema(BaseModel):
    question_id: str
    text: str
    question_type: str
    options: List[QuestionOption] = []
    is_essential: bool = True
    category: Optional[str] = None

class AnswerSubmission(BaseModel):
    question_id: str
    selected_value: str
    raw_text: Optional[str] = None

class AnswersPayload(BaseModel):
    answers: List[AnswerSubmission]

class TriageEvaluationResponse(BaseModel):
    incident_id: UUID
    priority_tier: PriorityTier
    urgency_score: int
    is_instant_p1_triggered: bool
    escalation_reason: Optional[str] = None
    is_triage_complete: bool = False
    next_adaptive_questions: List[QuestionSchema] = []

class CallIntakeRequest(BaseModel):
    caller_phone: str
    caller_name: Optional[str] = None
    latitude: float
    longitude: float
    address_landmark: str
    initial_incident_type: str

class DuplicateCheckRequest(BaseModel):
    latitude: float
    longitude: float
    incident_type: str
    landmark: Optional[str] = None
    reported_casualties: int = 1

class MergeCallRequest(BaseModel):
    call_id: UUID
    updated_casualty_count: int = 1
    additional_notes: Optional[str] = None

class DispatchConfirmRequest(BaseModel):
    incident_id: UUID
    recommendation_id: Optional[UUID] = None
    ambulance_id: UUID
    hospital_id: UUID
    operator_id: str
    is_override: bool = False
    override_reason: Optional[str] = None
