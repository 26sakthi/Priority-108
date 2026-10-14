import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal, engine, Base
from app.models.ambulance import Ambulance
from app.models.assignment import DispatchAssignment
from app.schemas.allocation import AmbulanceType, PriorityTier, AssignmentStatus
from app.services.auto_assignment_engine import select_best_ambulance

client = TestClient(app)

class MockAmbulance:
    def __init__(self, code, amb_type, status, lat, lon):
        self.ambulance_id = uuid.uuid4()
        self.vehicle_code = code
        self.ambulance_type = amb_type
        self.status = status
        self.latitude = lat
        self.longitude = lon

# --- Pure Algorithm Tests (Zero DB Dependency) ---

def test_pure_engine_allocates_fastest_eligible_als():
    """Verifies that an ALS requirement picks the nearest available ALS unit."""
    amb_als_near = MockAmbulance("AMB-ALS-NEAR", "ALS", "AVAILABLE", 11.2340, 78.8740)
    amb_als_far = MockAmbulance("AMB-ALS-FAR", "ALS", "AVAILABLE", 11.2900, 78.9200)
    amb_bls_very_near = MockAmbulance("AMB-BLS-VERY-NEAR", "BLS", "AVAILABLE", 11.2341, 78.8741)

    patient_lat, patient_lon = 11.2350, 78.8750

    winner, est, dist, rationale, is_downgrade = select_best_ambulance(
        ambulances=[amb_als_far, amb_als_near, amb_bls_very_near],
        patient_lat=patient_lat,
        patient_lon=patient_lon,
        required_capability=AmbulanceType.ALS,
        priority_tier=PriorityTier.P1_CRITICAL
    )

    assert winner is not None
    assert winner.vehicle_code == "AMB-ALS-NEAR"
    assert est > 0
    assert dist > 0
    assert is_downgrade is False
    assert "AMB-ALS-NEAR" in rationale

def test_pure_engine_conserves_als_when_bls_sufficient():
    """Verifies that BLS requirement picks BLS unit even if ALS is slightly closer, preserving ALS."""
    amb_als = MockAmbulance("AMB-ALS", "ALS", "AVAILABLE", 11.2345, 78.8745)
    amb_bls = MockAmbulance("AMB-BLS", "BLS", "AVAILABLE", 11.2355, 78.8755)

    patient_lat, patient_lon = 11.2340, 78.8740

    winner, est, dist, rationale, is_downgrade = select_best_ambulance(
        ambulances=[amb_als, amb_bls],
        patient_lat=patient_lat,
        patient_lon=patient_lon,
        required_capability=AmbulanceType.BLS,
        priority_tier=PriorityTier.P2_HIGH_URGENCY
    )

    assert winner is not None
    assert winner.vehicle_code == "AMB-BLS"
    assert is_downgrade is False

def test_pure_engine_p1_fallback_when_als_depleted():
    """Verifies that a critical P1 incident falls back to BLS if zero ALS are available."""
    amb_bls = MockAmbulance("AMB-BLS-BACKUP", "BLS", "AVAILABLE", 11.2350, 78.8750)
    amb_als_offline = MockAmbulance("AMB-ALS-OFF", "ALS", "OFFLINE", 11.2340, 78.8740)

    winner, est, dist, rationale, is_downgrade = select_best_ambulance(
        ambulances=[amb_bls, amb_als_offline],
        patient_lat=11.2340,
        patient_lon=78.8740,
        required_capability=AmbulanceType.ALS,
        priority_tier=PriorityTier.P1_CRITICAL
    )

    assert winner is not None
    assert winner.vehicle_code == "AMB-BLS-BACKUP"
    assert is_downgrade is True
    assert "DOWNGRADE DISPATCH" in rationale

def test_pure_engine_returns_none_when_fleet_exhausted():
    """Verifies graceful handling when all ambulances are busy."""
    amb_busy = MockAmbulance("AMB-BUSY", "ALS", "ASSIGNED", 11.2340, 78.8740)
    amb_off = MockAmbulance("AMB-OFF", "ALS", "OFFLINE", 11.2340, 78.8740)

    winner, est, dist, rationale, is_downgrade = select_best_ambulance(
        ambulances=[amb_busy, amb_off],
        patient_lat=11.2340,
        patient_lon=78.8740,
        required_capability=AmbulanceType.ALS,
        priority_tier=PriorityTier.P1_CRITICAL
    )

    assert winner is None
    assert est is None
    assert "currently committed" in rationale

# --- Full API & Database Integration Tests ---

@pytest.fixture(autouse=True)
def clean_db():
    """Ensures clean state for integration tests."""
    db = SessionLocal()
    try:
        # Clear test assignments
        db.query(DispatchAssignment).delete()
        # Reset ambulances
        db.query(Ambulance).update({"status": "AVAILABLE"})
        db.commit()
    finally:
        db.close()

def test_api_auto_assign_end_to_end():
    """Tests POST /api/v1/dispatch/auto-assign end-to-end against live DB."""
    test_incident_id = str(uuid.uuid4())
    payload = {
        "incident_id": test_incident_id,
        "latitude": 11.234123,
        "longitude": 78.874123,
        "required_capability": "ALS",
        "priority_tier": "P1_CRITICAL",
        "max_acceptable_est_seconds": 1800
    }

    response = client.post("/api/v1/dispatch/auto-assign", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["incident_id"] == test_incident_id
    assert data["assignment_status"] == "ASSIGNED"
    assert data["assigned_ambulance_id"] is not None
    assert data["est_travel_seconds"] > 0
    assert data["distance_meters"] > 0

    # Verify that the assigned ambulance is now marked ASSIGNED in DB
    db = SessionLocal()
    amb = db.query(Ambulance).filter(Ambulance.ambulance_id == data["assigned_ambulance_id"]).first()
    assert amb.status == "ASSIGNED"
    db.close()

def test_api_prevents_duplicate_active_assignment():
    """Verifies that duplicate assignment requests for the same incident return HTTP 409 Conflict."""
    test_incident_id = str(uuid.uuid4())
    payload = {
        "incident_id": test_incident_id,
        "latitude": 11.234123,
        "longitude": 78.874123,
        "required_capability": "BLS",
        "priority_tier": "P2_HIGH_URGENCY"
    }

    # First assignment succeeds
    res1 = client.post("/api/v1/dispatch/auto-assign", json=payload)
    assert res1.status_code == 200

    # Second assignment returns 409 Conflict
    res2 = client.post("/api/v1/dispatch/auto-assign", json=payload)
    assert res2.status_code == 409
    err = res2.json()
    assert err["detail"]["code"] == "INCIDENT_ALREADY_ASSIGNED"

def test_api_queues_when_all_units_offline():
    """Verifies that when all units are offline, API returns 200 with QUEUED_AWAITING_UNIT."""
    db = SessionLocal()
    db.query(Ambulance).update({"status": "OFFLINE"})
    db.commit()
    db.close()

    test_incident_id = str(uuid.uuid4())
    payload = {
        "incident_id": test_incident_id,
        "latitude": 11.234123,
        "longitude": 78.874123,
        "required_capability": "ALS",
        "priority_tier": "P1_CRITICAL"
    }

    response = client.post("/api/v1/dispatch/auto-assign", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["assignment_status"] == "QUEUED_AWAITING_UNIT"
    assert data["assigned_ambulance_id"] is None
    assert "Incident queued" in response.json()["message"]
