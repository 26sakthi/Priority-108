import pytest
from fastapi.testclient import TestClient
from app.main import app
from db.database import Base, engine
from db.seed_demo_data import seed_database

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    seed_database()
    with TestClient(app) as test_client:
        yield test_client

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "HEALTHY"

def test_scenario_1_instant_p1_intake_flow(client):
    """
    Scenario 1: Call intake with absent breathing triggers immediate P1 escalation.
    """
    # 1. Start intake
    intake_res = client.post("/api/v1/calls/intake", json={
        "caller_phone": "+919876543210",
        "caller_name": "Karthik Raja",
        "latitude": 11.234123,
        "longitude": 78.874123,
        "address_landmark": "NH-45 Samayapuram Toll",
        "initial_incident_type": "ROAD_TRAFFIC_ACCIDENT"
    })
    assert intake_res.status_code == 201
    data = intake_res.json()["data"]
    call_id = data["call_id"]
    inc_id = data["provisional_incident_id"]
    assert len(data["questions"]) >= 5

    # 2. Submit answer: absent breathing
    answers_res = client.post(f"/api/v1/calls/{call_id}/answers", json={
        "answers": [
            {"question_id": "Q_BREATHING", "selected_value": "ABSENT"},
            {"question_id": "Q_CONSCIOUSNESS", "selected_value": "UNRESPONSIVE"}
        ]
    })
    assert answers_res.status_code == 200
    triage_data = answers_res.json()["data"]
    assert triage_data["priority_tier"] == "P1_CRITICAL"
    assert triage_data["urgency_score"] >= 95
    assert triage_data["is_instant_p1_triggered"] is True

def test_scenario_2_duplicate_call_merge(client):
    """
    Scenario 2: Duplicate detection clusters second call within 150m and updates casualties.
    """
    # 1. First call creates incident
    r1 = client.post("/api/v1/calls/intake", json={
        "caller_phone": "+919800000001",
        "caller_name": "Witness 1",
        "latitude": 11.244123,
        "longitude": 78.884123,
        "address_landmark": "Medical College Gate",
        "initial_incident_type": "ROAD_TRAFFIC_ACCIDENT"
    })
    inc_id = r1.json()["data"]["provisional_incident_id"]

    # 2. Check duplicate for second bystander 40m away
    dup_res = client.post("/api/v1/incidents/check-duplicate", json={
        "latitude": 11.244200,
        "longitude": 78.884200,
        "incident_type": "ROAD_TRAFFIC_ACCIDENT",
        "landmark": "Near Medical College Gate",
        "reported_casualties": 3
    })
    assert dup_res.status_code == 200
    dup_data = dup_res.json()["data"]
    assert dup_data["match_confidence"] == "HIGH_MATCH"

    # 3. Merge call into first incident with updated casualties = 3
    r2 = client.post("/api/v1/calls/intake", json={
        "caller_phone": "+919800000002",
        "caller_name": "Witness 2",
        "latitude": 11.244200,
        "longitude": 78.884200,
        "address_landmark": "Near Medical College Gate",
        "initial_incident_type": "ROAD_TRAFFIC_ACCIDENT"
    })
    call2_id = r2.json()["data"]["call_id"]

    merge_res = client.post(f"/api/v1/incidents/{inc_id}/merge-call", json={
        "call_id": call2_id,
        "updated_casualty_count": 3,
        "additional_notes": "Second caller confirms 3 victims trapped."
    })
    assert merge_res.status_code == 200
    assert merge_res.json()["data"]["affected_casualty_count"] == 3

def test_scenario_3_recommendations_and_routing(client):
    """
    Scenario 3: System provides top recommendations with Dijkstra routes.
    """
    # Query queue to get any active incident
    q_res = client.get("/api/v1/incidents?status=ACTIVE")
    incidents = q_res.json()["data"]["queue"]
    assert len(incidents) > 0
    inc_id = incidents[0]["incident_id"]

    rec_res = client.get(f"/api/v1/incidents/{inc_id}/recommendations")
    assert rec_res.status_code == 200
    recs = rec_res.json()["data"]["recommendations"]
    assert len(recs) > 0
    top = recs[0]
    assert top["rank"] == 1
    assert "ambulance" in top
    assert "receiving_hospital" in top
    assert len(top["scene_route"]["coordinates"]) >= 2
    assert len(top["hospital_route"]["coordinates"]) >= 2

def test_scenario_4_dispatch_confirm_and_audit(client):
    """
    Scenario 4: Dispatch confirm transitions incident to DISPATCHED and logs action.
    """
    q_res = client.get("/api/v1/incidents?status=ACTIVE")
    inc_id = q_res.json()["data"]["queue"][0]["incident_id"]

    rec_res = client.get(f"/api/v1/incidents/{inc_id}/recommendations")
    recs = rec_res.json()["data"]["recommendations"]
    top_rec = recs[0]

    confirm_res = client.post("/api/v1/dispatch/confirm", json={
        "incident_id": inc_id,
        "recommendation_id": top_rec["recommendation_id"],
        "ambulance_id": top_rec["ambulance"]["ambulance_id"],
        "hospital_id": top_rec["receiving_hospital"]["hospital_id"],
        "operator_id": "DISPATCHER_TN_042",
        "is_override": False
    })
    assert confirm_res.status_code == 200
    data = confirm_res.json()["data"]
    assert data["incident_status"] == "DISPATCHED"
    assert data["ambulance_status"] == "EN_ROUTE_SCENE"
    assert "action_id" in data
