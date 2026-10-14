from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from uuid import UUID
from app.schemas.domain import (
    IncidentStatus, PriorityTier, AmbulanceType, AmbulanceStatus,
    MatchConfidence, FacilitySpecialty, QuestionSchema
)

class ApiResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: str = "Operation completed successfully"

class ApiErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

class ApiErrorResponse(BaseModel):
    success: bool = False
    error: ApiErrorDetail

class CallIntakeData(BaseModel):
    call_id: UUID
    provisional_incident_id: UUID
    is_duplicate_detected: bool = False
    duplicate_info: Optional[Dict[str, Any]] = None
    questions: List[QuestionSchema]

class IncidentSummary(BaseModel):
    incident_id: UUID
    incident_number: str
    incident_type: str
    priority_tier: PriorityTier
    urgency_score: int
    affected_casualty_count: int
    status: IncidentStatus
    address_landmark: str
    latitude: float
    longitude: float
    is_trapped: bool = False
    scene_hazards: List[str] = []
    call_count: int = 1
    created_at: datetime
    assigned_ambulance: Optional[Dict[str, Any]] = None
    target_hospital: Optional[Dict[str, Any]] = None

class IncidentQueueResponse(BaseModel):
    total_active_incidents: int
    queue: List[IncidentSummary]

class DuplicateMatchInfo(BaseModel):
    incident_id: UUID
    incident_number: str
    distance_meters: int
    time_gap_seconds: int
    current_casualty_count: int
    projected_new_casualty_count: int
    current_priority_tier: PriorityTier

class DuplicateCheckResponse(BaseModel):
    match_confidence: MatchConfidence
    confidence_score: float
    matched_incident: Optional[DuplicateMatchInfo] = None
    recommendation: str
    rationale: str

class AmbulanceInfo(BaseModel):
    ambulance_id: UUID
    vehicle_code: str
    ambulance_type: AmbulanceType
    status: AmbulanceStatus
    latitude: float
    longitude: float
    base_station: str
    staff: List[str]
    equipment: List[str]

class HospitalInfo(BaseModel):
    hospital_id: UUID
    name: str
    latitude: float
    longitude: float
    specialties: List[FacilitySpecialty]
    icu_beds_available: int
    general_beds_available: int
    is_accepting_emergencies: bool
    contact_phone: Optional[str] = None
    eta_to_hospital_seconds: Optional[int] = None
    distance_to_hospital_meters: Optional[int] = None
    specialty_matched: Optional[str] = None

class GeoRouteGeometry(BaseModel):
    type: str = "LineString"
    coordinates: List[List[float]] # [[lon, lat], ...]

class RecommendationItem(BaseModel):
    recommendation_id: UUID
    rank: int
    ambulance: AmbulanceInfo
    eta_to_scene_seconds: int
    distance_to_scene_meters: int
    receiving_hospital: HospitalInfo
    suitability_score: float
    recommendation_rationale: str
    scene_route: GeoRouteGeometry
    hospital_route: GeoRouteGeometry

class RecommendationsResponse(BaseModel):
    incident_id: UUID
    incident_priority: PriorityTier
    recommendations: List[RecommendationItem]

class DispatchConfirmData(BaseModel):
    action_id: UUID
    incident_id: UUID
    incident_status: IncidentStatus
    ambulance_code: str
    ambulance_status: AmbulanceStatus
    confirmed_hospital: str
    dispatch_timestamp: datetime
