import uuid
import hashlib
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.models import Incident, CallReport, AssessmentAnswer, PriorityAssessment
from app.schemas.domain import (
    CallIntakeRequest, AnswersPayload, TriageEvaluationResponse,
    IncidentStatus, PriorityTier, MatchConfidence
)
from app.schemas.api_payloads import ApiResponse, CallIntakeData
from app.services.question_engine import question_engine
from app.services.priority_engine import priority_engine
from app.services.dedup_engine import dedup_engine

router = APIRouter(prefix="/calls", tags=["Call Intake & Triage"])

def hash_phone(phone: str) -> str:
    return hashlib.sha256((phone + "salt_2026").encode()).hexdigest()

@router.post("/intake", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def start_call_intake(payload: CallIntakeRequest, db: Session = Depends(get_db)):
    """
    Initiates emergency call intake session, checks for active spatial duplicates,
    creates provisional incident and returns the 5 essential screening questions.
    """
    # 1. Query active incidents for duplicate detection
    active_incidents = db.query(Incident).filter(
        Incident.status.in_(["REPORTED", "TRIAGED", "DISPATCHING", "DISPATCHED", "ON_SCENE"])
    ).all()

    conf, score, matched_inc, details = dedup_engine.check_duplicate(
        latitude=payload.latitude,
        longitude=payload.longitude,
        incident_type=payload.initial_incident_type,
        active_incidents=active_incidents,
        landmark=payload.address_landmark
    )

    is_dup = (conf == MatchConfidence.HIGH_MATCH and matched_inc is not None)
    
    # 2. Generate identifiers
    call_id = str(uuid.uuid4())
    inc_id = matched_inc.incident_id if is_dup else str(uuid.uuid4())
    inc_num = matched_inc.incident_number if is_dup else f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

    # 3. Create incident if not a high-confidence duplicate
    if not is_dup:
        incident = Incident(
            incident_id=inc_id,
            incident_number=inc_num,
            incident_type=payload.initial_incident_type,
            description=f"Emergency reported at {payload.address_landmark}",
            latitude=payload.latitude,
            longitude=payload.longitude,
            address_landmark=payload.address_landmark,
            status=IncidentStatus.REPORTED.value,
            priority_tier=PriorityTier.P2_HIGH_URGENCY.value,
            urgency_score=50,
            affected_casualty_count=1,
            call_count=1,
            created_at=datetime.utcnow()
        )
        db.add(incident)
        db.commit()
    else:
        # Increment call count on existing incident
        matched_inc.call_count += 1
        db.commit()

    # 4. Record CallReport
    call_report = CallReport(
        call_id=call_id,
        incident_id=inc_id,
        caller_phone_hash=hash_phone(payload.caller_phone),
        caller_name=payload.caller_name,
        reported_latitude=payload.latitude,
        reported_longitude=payload.longitude,
        reported_landmark=payload.address_landmark,
        reported_casualties=1,
        dedup_confidence=score if is_dup else None,
        call_start_time=datetime.utcnow()
    )
    db.add(call_report)
    db.commit()

    # 5. Fetch 5 Essential Questions
    questions = question_engine.get_essential_questions()

    return ApiResponse(
        success=True,
        data={
            "call_id": call_id,
            "provisional_incident_id": inc_id,
            "incident_number": inc_num,
            "is_duplicate_detected": is_dup,
            "duplicate_info": details if is_dup else None,
            "questions": [q.model_dump() for q in questions]
        },
        message="Call intake initialized"
    )

@router.post("/{call_id}/answers", response_model=ApiResponse)
def submit_answers(call_id: str, payload: AnswersPayload, db: Session = Depends(get_db)):
    """
    Submits operator answers, evaluates clinical triage urgency,
    triggers instant P1 fail-fast escalation if needed, or serves adaptive follow-ups.
    """
    call_report = db.query(CallReport).filter(CallReport.call_id == call_id).first()
    if not call_report:
        raise HTTPException(status_code=404, detail="Call record not found")

    incident = db.query(Incident).filter(Incident.incident_id == call_report.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Associated incident not found")

    # 1. Record individual answers
    for ans in payload.answers:
        answer_record = AssessmentAnswer(
            answer_id=str(uuid.uuid4()),
            incident_id=incident.incident_id,
            call_id=call_id,
            question_id=ans.question_id,
            selected_value=ans.selected_value,
            raw_answer_text=ans.raw_text,
            answered_at=datetime.utcnow()
        )
        db.add(answer_record)

    # 2. Run clinical priority evaluation
    tier, score, is_instant, reason, factors = priority_engine.evaluate(
        incident_type=incident.incident_type,
        answers=payload.answers,
        reported_casualties=incident.affected_casualty_count,
        hazards=incident.scene_hazards or []
    )

    # 3. Update Incident state & audit snapshot
    incident.priority_tier = tier.value
    incident.urgency_score = score
    if is_instant:
        incident.status = IncidentStatus.DISPATCHING.value
    else:
        incident.status = IncidentStatus.TRIAGED.value
    incident.updated_at = datetime.utcnow()

    # Create Priority Assessment audit snapshot
    audit_snapshot = PriorityAssessment(
        assessment_id=str(uuid.uuid4()),
        incident_id=incident.incident_id,
        calculated_score=score,
        assigned_tier=tier.value,
        rule_version=priority_engine.RULE_VERSION,
        contributing_factors=factors,
        is_instant_escalation=is_instant,
        created_at=datetime.utcnow()
    )
    db.add(audit_snapshot)
    db.commit()

    # 4. Determine adaptive follow-ups
    adaptive_questions = []
    if not is_instant:
        adaptive_questions = question_engine.get_adaptive_questions(incident.incident_type)

    return ApiResponse(
        success=True,
        data={
            "incident_id": incident.incident_id,
            "incident_number": incident.incident_number,
            "priority_tier": tier.value,
            "urgency_score": score,
            "is_instant_p1_triggered": is_instant,
            "escalation_reason": reason,
            "contributing_factors": factors,
            "is_triage_complete": is_instant or (len(adaptive_questions) == 0),
            "next_adaptive_questions": [q.model_dump() for q in adaptive_questions]
        },
        message="Answers processed and priority assessed"
    )
