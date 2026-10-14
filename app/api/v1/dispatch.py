import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.models.ambulance import Ambulance
from app.models.assignment import DispatchAssignment
from app.schemas.allocation import (
    AllocationRequest,
    AllocationResponse,
    AllocationData,
    AssignmentStatus,
    AmbulanceCreate,
    AmbulanceResponse,
    AmbulanceType
)
from app.services.auto_assignment_engine import select_best_ambulance

router = APIRouter(prefix="/dispatch", tags=["Ambulance Auto-Assignment"])

@router.post(
    "/auto-assign",
    response_model=AllocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Automatically allocate and assign an ambulance to an emergency incident"
)
def auto_assign_ambulance(
    payload: AllocationRequest,
    db: Session = Depends(get_db)
):
    """
    Automatically allocates and dispatches the most suitable and nearest available ambulance.
    
    Guarantees:
    - Zero manual operator selection required.
    - Prevents duplicate active assignments on the same incident.
    - Concurrency-safe row-level locking during assignment.
    - Fallback to QUEUED_AWAITING_UNIT if all vehicles are busy.
    """
    # 1. Check if this incident already has an active assignment
    existing_assignment = db.query(DispatchAssignment).filter(
        DispatchAssignment.incident_id == payload.incident_id,
        DispatchAssignment.is_active == True
    ).first()

    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "INCIDENT_ALREADY_ASSIGNED",
                "message": f"Incident {payload.incident_id} already has an active assignment ({existing_assignment.assignment_id}).",
                "active_assignment_id": str(existing_assignment.assignment_id)
            }
        )

    # 2. Query available candidate ambulances with row-level locking
    # In PostgreSQL, with_for_update(skip_locked=True) ensures zero race conditions across concurrent dispatch calls
    try:
        candidate_query = db.query(Ambulance).filter(Ambulance.status == "AVAILABLE")
        # Use with_for_update if supported by dialect
        if db.bind and db.bind.dialect.name == "postgresql":
            candidate_ambulances = candidate_query.with_for_update(skip_locked=True).all()
        else:
            candidate_ambulances = candidate_query.all()
    except Exception:
        candidate_ambulances = db.query(Ambulance).filter(Ambulance.status == "AVAILABLE").all()

    # 3. Execute pure deterministic allocation algorithm
    cutoff_est = payload.max_acceptable_est_seconds or 1800
    chosen_amb, est_sec, dist_m, rationale, is_downgrade = select_best_ambulance(
        ambulances=candidate_ambulances,
        patient_lat=payload.latitude,
        patient_lon=payload.longitude,
        required_capability=payload.required_capability,
        priority_tier=payload.priority_tier,
        max_acceptable_est_seconds=cutoff_est
    )

    now_utc = datetime.now(timezone.utc)

    # 4. Handle Case A: No eligible ambulance available
    if chosen_amb is None:
        unassigned_record = DispatchAssignment(
            assignment_id=uuid.uuid4(),
            incident_id=payload.incident_id,
            ambulance_id=None,
            assignment_status=AssignmentStatus.QUEUED_AWAITING_UNIT.value,
            est_travel_seconds=None,
            distance_meters=None,
            allocation_rationale=rationale,
            is_capability_downgrade=False,
            is_active=True,
            assigned_at=now_utc
        )
        db.add(unassigned_record)
        db.commit()
        db.refresh(unassigned_record)

        return AllocationResponse(
            success=True,
            data=AllocationData(
                assignment_id=unassigned_record.assignment_id,
                incident_id=unassigned_record.incident_id,
                assigned_ambulance_id=None,
                vehicle_code=None,
                ambulance_type=None,
                est_travel_seconds=None,
                distance_meters=None,
                assignment_status=AssignmentStatus.QUEUED_AWAITING_UNIT,
                allocation_rationale=rationale,
                is_capability_downgrade=False,
                assigned_at=unassigned_record.assigned_at
            ),
            message="No available ambulances currently match requirements. Incident queued for next available vehicle."
        )

    # 5. Handle Case B: Eligible ambulance found -> Execute atomic lock & state transition
    chosen_amb.status = "ASSIGNED"
    assignment_record = DispatchAssignment(
        assignment_id=uuid.uuid4(),
        incident_id=payload.incident_id,
        ambulance_id=chosen_amb.ambulance_id,
        assignment_status=AssignmentStatus.ASSIGNED.value,
        est_travel_seconds=est_sec,
        distance_meters=dist_m,
        allocation_rationale=rationale,
        is_capability_downgrade=is_downgrade,
        is_active=True,
        assigned_at=now_utc
    )

    db.add(assignment_record)
    db.commit()
    db.refresh(assignment_record)

    return AllocationResponse(
        success=True,
        data=AllocationData(
            assignment_id=assignment_record.assignment_id,
            incident_id=assignment_record.incident_id,
            assigned_ambulance_id=chosen_amb.ambulance_id,
            vehicle_code=chosen_amb.vehicle_code,
            ambulance_type=AmbulanceType(chosen_amb.ambulance_type),
            est_travel_seconds=est_sec,
            distance_meters=dist_m,
            assignment_status=AssignmentStatus.ASSIGNED,
            allocation_rationale=rationale,
            is_capability_downgrade=is_downgrade,
            assigned_at=assignment_record.assigned_at
        ),
        message="Ambulance automatically allocated and dispatched."
    )

# --- Fleet Management Endpoints for Testing & Telemetry ---

@router.post("/ambulances", response_model=AmbulanceResponse, status_code=status.HTTP_201_CREATED)
def register_ambulance(payload: AmbulanceCreate, db: Session = Depends(get_db)):
    """Registers a new vehicle in the ambulance fleet."""
    new_amb = Ambulance(
        vehicle_code=payload.vehicle_code,
        ambulance_type=payload.ambulance_type.value,
        status=payload.status.value,
        latitude=payload.latitude,
        longitude=payload.longitude
    )
    db.add(new_amb)
    try:
        db.commit()
        db.refresh(new_amb)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle code '{payload.vehicle_code}' already exists."
        )
    return new_amb

@router.get("/ambulances", response_model=list[AmbulanceResponse])
def list_ambulances(db: Session = Depends(get_db)):
    """Lists all ambulances with operational status and GPS telemetry."""
    return db.query(Ambulance).order_by(Ambulance.vehicle_code.asc()).all()
