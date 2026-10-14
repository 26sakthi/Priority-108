import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Hospital(Base):
    __tablename__ = "hospitals"

    hospital_id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    specialties = Column(JSON, default=list, nullable=False) # List of specialty strings
    icu_beds_available = Column(Integer, default=0, nullable=False)
    general_beds_available = Column(Integer, default=0, nullable=False)
    is_accepting_emergencies = Column(Boolean, default=True, nullable=False)
    contact_phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    recommendations = relationship("DispatchRecommendation", back_populates="hospital")
    dispatch_actions = relationship("DispatchAction", back_populates="hospital")

class Ambulance(Base):
    __tablename__ = "ambulances"

    ambulance_id = Column(String(36), primary_key=True, default=generate_uuid)
    vehicle_code = Column(String(50), unique=True, nullable=False)
    ambulance_type = Column(String(20), nullable=False) # ALS, BLS, PTS
    status = Column(String(30), default="AVAILABLE", nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    base_station_name = Column(String(255), nullable=False)
    staff_qualifications = Column(JSON, default=list, nullable=False)
    onboard_equipment = Column(JSON, default=list, nullable=False)
    current_incident_id = Column(String(36), nullable=True)
    last_location_update = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    recommendations = relationship("DispatchRecommendation", back_populates="ambulance")
    dispatch_actions = relationship("DispatchAction", back_populates="ambulance")

class Incident(Base):
    __tablename__ = "incidents"

    incident_id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_number = Column(String(50), unique=True, nullable=False)
    incident_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address_landmark = Column(String(255), nullable=False)
    status = Column(String(30), default="REPORTED", nullable=False)
    priority_tier = Column(String(20), default="P2_HIGH_URGENCY", nullable=False)
    urgency_score = Column(Integer, default=50, nullable=False)
    affected_casualty_count = Column(Integer, default=1, nullable=False)
    is_trapped = Column(Boolean, default=False, nullable=False)
    scene_hazards = Column(JSON, default=list, nullable=False)
    active_ambulance_id = Column(String(36), ForeignKey("ambulances.ambulance_id"), nullable=True)
    target_hospital_id = Column(String(36), ForeignKey("hospitals.hospital_id"), nullable=True)
    call_count = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    call_reports = relationship("CallReport", back_populates="incident", cascade="all, delete-orphan")
    answers = relationship("AssessmentAnswer", back_populates="incident", cascade="all, delete-orphan")
    assessments = relationship("PriorityAssessment", back_populates="incident", cascade="all, delete-orphan")
    recommendations = relationship("DispatchRecommendation", back_populates="incident", cascade="all, delete-orphan")
    actions = relationship("DispatchAction", back_populates="incident")

class CallReport(Base):
    __tablename__ = "call_reports"

    call_id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False)
    caller_phone_hash = Column(String(128), nullable=False)
    caller_name = Column(String(100), nullable=True)
    reported_latitude = Column(Float, nullable=False)
    reported_longitude = Column(Float, nullable=False)
    reported_landmark = Column(String(255), nullable=True)
    reported_casualties = Column(Integer, default=1, nullable=False)
    caller_statement = Column(Text, nullable=True)
    dedup_confidence = Column(Float, nullable=True)
    call_start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    call_end_time = Column(DateTime, nullable=True)

    incident = relationship("Incident", back_populates="call_reports")
    answers = relationship("AssessmentAnswer", back_populates="call_report", cascade="all, delete-orphan")

class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"

    answer_id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False)
    call_id = Column(String(36), ForeignKey("call_reports.call_id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(100), nullable=False)
    selected_value = Column(String(100), nullable=False)
    raw_answer_text = Column(Text, nullable=True)
    answered_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    incident = relationship("Incident", back_populates="answers")
    call_report = relationship("CallReport", back_populates="answers")

class PriorityAssessment(Base):
    __tablename__ = "priority_assessments"

    assessment_id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False)
    calculated_score = Column(Integer, nullable=False)
    assigned_tier = Column(String(20), nullable=False)
    rule_version = Column(String(50), nullable=False)
    contributing_factors = Column(JSON, default=list, nullable=False)
    is_instant_escalation = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    incident = relationship("Incident", back_populates="assessments")

class DispatchRecommendation(Base):
    __tablename__ = "dispatch_recommendations"

    recommendation_id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False)
    ambulance_id = Column(String(36), ForeignKey("ambulances.ambulance_id"), nullable=False)
    hospital_id = Column(String(36), ForeignKey("hospitals.hospital_id"), nullable=False)
    eta_to_scene_seconds = Column(Integer, nullable=False)
    distance_to_scene_meters = Column(Integer, nullable=False)
    eta_to_hospital_seconds = Column(Integer, nullable=False)
    distance_to_hospital_meters = Column(Integer, nullable=False)
    suitability_match_score = Column(Float, nullable=False)
    suitability_reason = Column(Text, nullable=False)
    scene_route_geometry = Column(JSON, nullable=False)
    hospital_route_geometry = Column(JSON, nullable=False)
    is_selected = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    incident = relationship("Incident", back_populates="recommendations")
    ambulance = relationship("Ambulance", back_populates="recommendations")
    hospital = relationship("Hospital", back_populates="recommendations")

class DispatchAction(Base):
    __tablename__ = "dispatch_actions"

    action_id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.incident_id"), nullable=False)
    recommendation_id = Column(String(36), ForeignKey("dispatch_recommendations.recommendation_id"), nullable=True)
    ambulance_id = Column(String(36), ForeignKey("ambulances.ambulance_id"), nullable=False)
    hospital_id = Column(String(36), ForeignKey("hospitals.hospital_id"), nullable=False)
    operator_id = Column(String(100), nullable=False)
    is_override = Column(Boolean, default=False, nullable=False)
    override_reason = Column(Text, nullable=True)
    action_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    incident = relationship("Incident", back_populates="actions")
    ambulance = relationship("Ambulance", back_populates="dispatch_actions")
    hospital = relationship("Hospital", back_populates="dispatch_actions")
