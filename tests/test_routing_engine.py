import pytest
from app.services.routing_engine import routing_engine
from app.models.models import Hospital

def test_dijkstra_path_calculation():
    # From Perambalur Bus Stand to Samayapuram Toll
    dist, duration, coords = routing_engine.calculate_dijkstra_route(
        11.234123, 78.874123,
        11.214123, 78.854123
    )
    assert dist > 1000
    assert duration > 60
    assert len(coords) >= 2
    # Coordinates in GeoJSON format [lon, lat]
    assert len(coords[0]) == 2
    assert 78.0 <= coords[0][0] <= 79.5 # lon
    assert 10.0 <= coords[0][1] <= 12.0 # lat

def test_specialty_hospital_preferred_for_severe_trauma():
    hosp_trauma = Hospital(
        hospital_id="h-ds-med",
        name="Dhanalakshmi Srinivasan Medical College Hospital",
        latitude=11.244123,
        longitude=78.884123,
        specialties=["TRAUMA_LEVEL_1", "CARDIAC_CATH_LAB"],
        icu_beds_available=4,
        is_accepting_emergencies=True
    )
    hosp_clinic = Hospital(
        hospital_id="h-clinic",
        name="Nearby Clinic",
        latitude=11.235123,
        longitude=78.875123,
        specialties=["GENERAL_EMERGENCY"],
        icu_beds_available=0,
        is_accepting_emergencies=True
    )

    rankings = routing_engine.select_best_hospital_for_incident(
        incident_lat=11.234123,
        incident_lon=78.874123,
        incident_type="ROAD_TRAFFIC_ACCIDENT",
        priority_tier="P1_CRITICAL",
        hospitals=[hosp_clinic, hosp_trauma]
    )

    # Dhanalakshmi Srinivasan Hospital must be selected first because clinic lacks Trauma Level 1 ICU!
    top_hospital = rankings[0][0]
    assert top_hospital.name == "Dhanalakshmi Srinivasan Medical College Hospital"
    assert "TRAUMA_LEVEL_1" in rankings[0][4]
