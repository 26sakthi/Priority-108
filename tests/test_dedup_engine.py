import pytest
from datetime import datetime, timedelta
from app.services.dedup_engine import dedup_engine, haversine_distance
from app.models.models import Incident
from app.schemas.domain import MatchConfidence

def test_haversine_distance_accuracy():
    # Perambalur Bus Stand to Samayapuram Toll ~ 3.5 km
    dist = haversine_distance(11.234123, 78.874123, 11.214123, 78.854123)
    assert 3000 < dist < 4000

def test_duplicate_detected_within_500m():
    inc = Incident(
        incident_id="test-inc-1",
        incident_number="INC-20261014-0001",
        incident_type="ROAD_TRAFFIC_ACCIDENT",
        latitude=11.234123,
        longitude=78.874123,
        address_landmark="NH-45 Samayapuram Toll Plaza",
        affected_casualty_count=1,
        priority_tier="P1_CRITICAL",
        created_at=datetime.utcnow() - timedelta(minutes=2)
    )

    # Caller 2 reports 35 meters away, same type, 2 min later
    conf, score, matched_inc, details = dedup_engine.check_duplicate(
        latitude=11.234180,
        longitude=78.874195,
        incident_type="ROAD_TRAFFIC_ACCIDENT",
        active_incidents=[inc],
        landmark="Near Samayapuram Toll Plaza",
        reported_casualties=2
    )

    assert conf == MatchConfidence.HIGH_MATCH
    assert score >= 0.85
    assert matched_inc.incident_id == "test-inc-1"
    assert details["projected_new_casualty_count"] == 2

def test_no_match_for_distant_location():
    inc = Incident(
        incident_id="test-inc-2",
        incident_number="INC-20261014-0002",
        incident_type="ROAD_TRAFFIC_ACCIDENT",
        latitude=11.234123,
        longitude=78.874123,
        address_landmark="Perambalur",
        created_at=datetime.utcnow()
    )

    # 15 km away
    conf, score, matched_inc, _ = dedup_engine.check_duplicate(
        latitude=11.350000,
        longitude=78.950000,
        incident_type="ROAD_TRAFFIC_ACCIDENT",
        active_incidents=[inc]
    )

    assert conf == MatchConfidence.NO_MATCH
    assert matched_inc is None
