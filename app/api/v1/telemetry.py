from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.models import Ambulance, Hospital
from app.schemas.api_payloads import ApiResponse

router = APIRouter(tags=["Fleet & Hospital Telemetry"])

class StatusUpdatePayload(BaseModel):
    status: str

@router.get("/ambulances", response_model=ApiResponse)
def get_ambulances(db: Session = Depends(get_db)):
    """Returns list of all ambulances with live coordinates, status, and onboard equipment."""
    ambulances = db.query(Ambulance).all()
    data = [
        {
            "ambulance_id": a.ambulance_id,
            "vehicle_code": a.vehicle_code,
            "ambulance_type": a.ambulance_type,
            "status": a.status,
            "latitude": a.latitude,
            "longitude": a.longitude,
            "base_station": a.base_station_name,
            "staff": a.staff_qualifications or [],
            "equipment": a.onboard_equipment or [],
            "current_incident_id": a.current_incident_id,
            "last_update": a.last_location_update.isoformat() if a.last_location_update else None
        }
        for a in ambulances
    ]
    return ApiResponse(success=True, data=data, message="Ambulance fleet retrieved")

@router.patch("/ambulances/{ambulance_id}/status", response_model=ApiResponse)
def update_ambulance_status(ambulance_id: str, payload: StatusUpdatePayload, db: Session = Depends(get_db)):
    """Updates operational status of an ambulance unit."""
    amb = db.query(Ambulance).filter(Ambulance.ambulance_id == ambulance_id).first()
    if not amb:
        raise HTTPException(status_code=404, detail="Ambulance not found")
    amb.status = payload.status
    amb.last_location_update = datetime.utcnow()
    db.commit()
    return ApiResponse(success=True, data={"ambulance_id": amb.ambulance_id, "status": amb.status}, message="Status updated")

@router.get("/hospitals", response_model=ApiResponse)
def get_hospitals(db: Session = Depends(get_db)):
    """Returns regional hospitals directory, open ICU/general beds, and clinical specialties."""
    hospitals = db.query(Hospital).all()
    data = [
        {
            "hospital_id": h.hospital_id,
            "name": h.name,
            "latitude": h.latitude,
            "longitude": h.longitude,
            "specialties": h.specialties or [],
            "icu_beds_available": h.icu_beds_available,
            "general_beds_available": h.general_beds_available,
            "is_accepting_emergencies": h.is_accepting_emergencies,
            "contact_phone": h.contact_phone
        }
        for h in hospitals
    ]
    return ApiResponse(success=True, data=data, message="Hospital directory retrieved")
