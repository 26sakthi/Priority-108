import pytest
from app.services.priority_engine import priority_engine
from app.schemas.domain import PriorityTier, AnswerSubmission

def test_instant_p1_on_absent_breathing():
    answers = [
        AnswerSubmission(question_id="Q_BREATHING", selected_value="ABSENT"),
        AnswerSubmission(question_id="Q_CONSCIOUSNESS", selected_value="UNRESPONSIVE"),
    ]
    tier, score, is_instant, reason, factors = priority_engine.evaluate(
        incident_type="ROAD_TRAFFIC_ACCIDENT",
        answers=answers
    )
    assert tier == PriorityTier.P1_CRITICAL
    assert score >= 95
    assert is_instant is True
    assert "Respiration ABSENT" in factors[0]

def test_p2_urgency_stable_breathing():
    answers = [
        AnswerSubmission(question_id="Q_CONSCIOUSNESS", selected_value="ALERT"),
        AnswerSubmission(question_id="Q_BREATHING", selected_value="NORMAL"),
        AnswerSubmission(question_id="Q_BLEEDING", selected_value="MODERATE"),
    ]
    tier, score, is_instant, reason, factors = priority_engine.evaluate(
        incident_type="ROAD_TRAFFIC_ACCIDENT",
        answers=answers
    )
    assert tier == PriorityTier.P2_HIGH_URGENCY
    assert is_instant is False
    assert 45 <= score < 80

def test_multi_casualty_score_boost():
    answers = [
        AnswerSubmission(question_id="Q_CONSCIOUSNESS", selected_value="ALERT"),
        AnswerSubmission(question_id="Q_BREATHING", selected_value="NORMAL"),
    ]
    _, score_1, _, _, _ = priority_engine.evaluate(
        incident_type="ROAD_TRAFFIC_ACCIDENT",
        answers=answers,
        reported_casualties=1
    )
    _, score_multi, _, _, _ = priority_engine.evaluate(
        incident_type="ROAD_TRAFFIC_ACCIDENT",
        answers=answers,
        reported_casualties=3
    )
    assert score_multi > score_1
