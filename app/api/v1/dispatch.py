import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.models import Incident, Ambulance, Hospital, DispatchAction
from app.schemas.domain import DispatchConfirmRequest, IncidentStatus, AmbulanceStatus
from app.schemas.api_payloads import ApiResponse

router = APIRouter(prefix="/dispatch", tags=["Dispatch Action & Audit"])

@router.post("/confirm", response_model=ApiResponse)
def confirm_dispatch(payload: DispatchConfirmRequest, db: Session = Depends(get_db)):
    """
    Operator confirms a recommendation or executes a manual override.
    Transitions incident to DISPATCHED, ambulance to EN_ROUTE_SCENE,
    and logs immutable operator action in dispatch_actions.
    """
    incident = db.query(Incident).filter(Incident.incident_id == str(payload.incident_id)).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    ambulance = db.query(Ambulance).filter(Ambulance.ambulance_id == str(payload.ambulance_id)).first()
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found")

    hospital = db.query(Hospital).filter(Hospital.hospital_id == str(payload.hospital_id)).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    # Update states
    incident.status = IncidentStatus.DISPATCHED.value
    incident.active_ambulance_id = ambulance.ambulance_id
    incident.target_hospital_id = hospital.hospital_id
    incident.updated_at = datetime.utcnow()

    ambulance.status = AmbulanceStatus.EN_ROUTE_SCENE.value
    ambulance.current_incident_id = incident.incident_id
    ambulance.last_location_update = datetime.utcnow()

    # Create immutable audit action
    action_id = str(uuid.uuid4())
    audit_action = DispatchAction(
        action_id=action_id,
        incident_id=incident.incident_id,
        recommendation_id=str(payload.recommendation_id) if payload.recommendation_id else None,
        ambulance_id=ambulance.ambulance_id,
        hospital_id=hospital.hospital_id,
        operator_id=payload.operator_id,
        is_override=payload.is_override,
        override_reason=payload.override_reason if payload.is_override else None,
        action_timestamp=datetime.utcnow()
    )
    db.add(audit_action)
    db.commit()

    return ApiResponse(
        success=True,
        data={
            "action_id": action_id,
            "incident_id": incident.incident_id,
            "incident_number": incident.incident_number,
            "incident_status": incident.status,
            "ambulance_code": ambulance.vehicle_code,
            "ambulance_status": ambulance.status,
            "confirmed_hospital": hospital.name,
            "dispatch_timestamp": audit_action.action_timestamp.isoformat()
        },
        message="Ambulance successfully dispatched"
    )
