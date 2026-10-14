from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import case, desc, asc

from app.api.deps import get_db
from app.models.models import (
    Incident, Ambulance, Hospital, CallReport, DispatchRecommendation
)
from app.schemas.domain import (
    DuplicateCheckRequest, MergeCallRequest, PriorityTier,
    IncidentStatus, MatchConfidence
)
from app.schemas.api_payloads import (
    ApiResponse, DuplicateCheckResponse, DuplicateMatchInfo
)
from app.services.dedup_engine import dedup_engine
from app.services.allocation_engine import allocation_engine

router = APIRouter(prefix="/incidents", tags=["Incidents & Priority Queue"])

@router.get("", response_model=ApiResponse)
def get_incident_queue(
    status_filter: Optional[str] = Query("ACTIVE", alias="status"),
    db: Session = Depends(get_db)
):
    """
    Returns prioritized queue of active incidents sorted by:
    1. Priority Tier (P1_CRITICAL > P2_HIGH_URGENCY > P3_LOWER_URGENCY)
    2. Urgency Score (100 -> 0 DESC)
    3. Creation Time (ASC)
    """
    query = db.query(Incident)

    if status_filter == "ACTIVE":
        query = query.filter(Incident.status.in_(["REPORTED", "TRIAGED", "DISPATCHING", "DISPATCHED", "ON_SCENE", "TRANSPORTING"]))
    elif status_filter:
        query = query.filter(Incident.status == status_filter)

    # Custom SQL sort order for Priority Tier
    tier_order = case(
        (Incident.priority_tier == PriorityTier.P1_CRITICAL.value, 1),
        (Incident.priority_tier == PriorityTier.P2_HIGH_URGENCY.value, 2),
        (Incident.priority_tier == PriorityTier.P3_LOWER_URGENCY.value, 3),
        else_=4
    )

    incidents = query.order_by(tier_order, desc(Incident.urgency_score), asc(Incident.created_at)).all()

    queue_data = []
    for inc in incidents:
        # Check assigned ambulance info
        assigned_amb = None
        if inc.active_ambulance_id:
            amb = db.query(Ambulance).filter(Ambulance.ambulance_id == inc.active_ambulance_id).first()
            if amb:
                assigned_amb = {
                    "ambulance_id": amb.ambulance_id,
                    "vehicle_code": amb.vehicle_code,
                    "ambulance_type": amb.ambulance_type,
                    "status": amb.status
                }

        target_hosp = None
        if inc.target_hospital_id:
            hosp = db.query(Hospital).filter(Hospital.hospital_id == inc.target_hospital_id).first()
            if hosp:
                target_hosp = {
                    "hospital_id": hosp.hospital_id,
                    "name": hosp.name
                }

        queue_data.append({
            "incident_id": inc.incident_id,
            "incident_number": inc.incident_number,
            "incident_type": inc.incident_type,
            "description": inc.description,
            "priority_tier": inc.priority_tier,
            "urgency_score": inc.urgency_score,
            "affected_casualty_count": inc.affected_casualty_count,
            "status": inc.status,
            "address_landmark": inc.address_landmark,
            "latitude": inc.latitude,
            "longitude": inc.longitude,
            "is_trapped": inc.is_trapped,
            "scene_hazards": inc.scene_hazards or [],
            "call_count": inc.call_count,
            "created_at": inc.created_at.isoformat() if inc.created_at else None,
            "assigned_ambulance": assigned_amb,
            "target_hospital": target_hosp
        })

    return ApiResponse(
        success=True,
        data={
            "total_active_incidents": len(queue_data),
            "queue": queue_data
        },
        message="Active incident queue retrieved"
    )

@router.get("/{incident_id}", response_model=ApiResponse)
def get_incident_dossier(incident_id: str, db: Session = Depends(get_db)):
    """Retrieves full incident dossier with calls and audit history."""
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    calls = [
        {
            "call_id": c.call_id,
            "caller_name": c.caller_name,
            "landmark": c.reported_landmark,
            "casualties": c.reported_casualties,
            "statement": c.caller_statement,
            "time": c.call_start_time.isoformat() if c.call_start_time else None
        }
        for c in inc.call_reports
    ]

    return ApiResponse(
        success=True,
        data={
            "incident_id": inc.incident_id,
            "incident_number": inc.incident_number,
            "incident_type": inc.incident_type,
            "status": inc.status,
            "priority_tier": inc.priority_tier,
            "urgency_score": inc.urgency_score,
            "affected_casualty_count": inc.affected_casualty_count,
            "latitude": inc.latitude,
            "longitude": inc.longitude,
            "address_landmark": inc.address_landmark,
            "call_count": inc.call_count,
            "calls": calls
        },
        message="Incident dossier retrieved"
    )

@router.post("/check-duplicate", response_model=ApiResponse)
def check_duplicate_incident(payload: DuplicateCheckRequest, db: Session = Depends(get_db)):
    """Analyzes whether an incoming call matches an active incident within spatial radius and temporal window."""
    active_incidents = db.query(Incident).filter(
        Incident.status.in_(["REPORTED", "TRIAGED", "DISPATCHING", "DISPATCHED", "ON_SCENE"])
    ).all()

    conf, score, matched_inc, details = dedup_engine.check_duplicate(
        latitude=payload.latitude,
        longitude=payload.longitude,
        incident_type=payload.incident_type,
        active_incidents=active_incidents,
        landmark=payload.landmark,
        reported_casualties=payload.reported_casualties
    )

    matched_payload = None
    if matched_inc and details:
        matched_payload = {
            "incident_id": matched_inc.incident_id,
            "incident_number": matched_inc.incident_number,
            "distance_meters": details["distance_meters"],
            "time_gap_seconds": details["time_gap_seconds"],
            "current_casualty_count": details["current_casualty_count"],
            "projected_new_casualty_count": details["projected_new_casualty_count"],
            "current_priority_tier": details["current_priority_tier"]
        }

    recommendation = "AUTO_MERGE_SUGGESTED" if conf == MatchConfidence.HIGH_MATCH else (
        "OPERATOR_REVIEW_REQUIRED" if conf == MatchConfidence.UNCERTAIN_MATCH else "CREATE_NEW_INCIDENT"
    )

    rationale = f"Confidence score: {int(score * 100)}%."
    if details:
        rationale += f" Distance: {details['distance_meters']}m away, time gap: {int(details['time_gap_seconds']/60)} min."

    return ApiResponse(
        success=True,
        data={
            "match_confidence": conf.value,
            "confidence_score": score,
            "matched_incident": matched_payload,
            "recommendation": recommendation,
            "rationale": rationale
        },
        message="Duplicate analysis complete"
    )

@router.post("/{incident_id}/merge-call", response_model=ApiResponse)
def merge_call_to_incident(incident_id: str, payload: MergeCallRequest, db: Session = Depends(get_db)):
    """
    Merges a call into an existing incident, preserving cumulative casualty counts
    (taking max of current vs reported) without destroying original incident data.
    """
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    call_report = db.query(CallReport).filter(CallReport.call_id == str(payload.call_id)).first()
    if call_report:
        call_report.incident_id = incident.incident_id
        if payload.additional_notes:
            call_report.caller_statement = (call_report.caller_statement or "") + f" | Update: {payload.additional_notes}"

    # Cumulative casualty invariant: never decrease casualty count!
    incident.affected_casualty_count = max(incident.affected_casualty_count, payload.updated_casualty_count)
    incident.call_count += 1
    incident.updated_at = datetime.utcnow()
    db.commit()

    return ApiResponse(
        success=True,
        data={
            "incident_id": incident.incident_id,
            "incident_number": incident.incident_number,
            "call_count": incident.call_count,
            "affected_casualty_count": incident.affected_casualty_count,
            "updated_at": incident.updated_at.isoformat()
        },
        message="Call successfully linked to incident"
    )

@router.get("/{incident_id}/recommendations", response_model=ApiResponse)
def get_dispatch_recommendations(incident_id: str, db: Session = Depends(get_db)):
    """
    Runs Allocation Engine & Dijkstra Hospital Routing Engine to return
    top 3 ranked ambulance + hospital recommendations with GeoJSON route geometry.
    """
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    ambulances = db.query(Ambulance).all()
    hospitals = db.query(Hospital).all()

    recommendations = allocation_engine.rank_recommendations(incident, ambulances, hospitals)

    return ApiResponse(
        success=True,
        data={
            "incident_id": incident.incident_id,
            "incident_priority": incident.priority_tier,
            "recommendations": [r.model_dump() for r in recommendations]
        },
        message="Recommendations generated successfully"
    )
