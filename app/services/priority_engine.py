from typing import List, Dict, Any, Tuple
from app.schemas.domain import PriorityTier, AnswerSubmission

CATEGORY_BASE_WEIGHTS = {
    "CARDIAC_CHEST_PAIN": 40,
    "RESPIRATORY": 40,
    "ROAD_TRAFFIC_ACCIDENT": 30,
    "UNCONSCIOUS_FALL": 35,
    "STROKE_NEURO": 35,
    "OTHER": 15
}

class PriorityEngine:
    RULE_VERSION = "TRIAGE-RULE-v1.0"

    def evaluate(
        self,
        incident_type: str,
        answers: List[AnswerSubmission],
        reported_casualties: int = 1,
        hazards: List[str] = None
    ) -> Tuple[PriorityTier, int, bool, str, List[str]]:
        """
        Returns:
            (priority_tier, urgency_score, is_instant_p1, escalation_reason, contributing_factors)
        """
        hazards = hazards or []
        answer_map = {a.question_id: a.selected_value for a in answers}
        contributing_factors = []
        
        # 1. Check Fail-Fast Instant P1 Escalation
        breathing = answer_map.get("Q_BREATHING")
        consciousness = answer_map.get("Q_CONSCIOUSNESS")
        bleeding = answer_map.get("Q_BLEEDING")

        if breathing == "ABSENT":
            contributing_factors.append("Critical vital: Respiration ABSENT / Gasping (+100)")
            contributing_factors.append("Instant P1 Fail-Fast Protocol triggered (<10s)")
            return (
                PriorityTier.P1_CRITICAL,
                98,
                True,
                "Patient is unresponsive with absent breathing. Immediate P1 escalation engaged.",
                contributing_factors
            )

        if bleeding == "SEVERE_PUMPING":
            contributing_factors.append("Critical vital: Severe arterial pumping hemorrhage (+45)")
            contributing_factors.append("Instant P1 Fail-Fast Protocol triggered (<10s)")
            return (
                PriorityTier.P1_CRITICAL,
                95,
                True,
                "Severe arterial hemorrhage detected. Immediate P1 escalation engaged.",
                contributing_factors
            )

        if consciousness == "UNRESPONSIVE" and breathing == "DIFFICULT":
            contributing_factors.append("Unresponsive patient with severe respiratory distress (+75)")
            contributing_factors.append("Instant P1 Fail-Fast Protocol triggered")
            return (
                PriorityTier.P1_CRITICAL,
                90,
                True,
                "Patient is unresponsive with severe breathing difficulty. Immediate P1 escalation engaged.",
                contributing_factors
            )

        # 2. Cumulative Urgency Score Calculation
        base_weight = CATEGORY_BASE_WEIGHTS.get(incident_type, 20)
        score = base_weight
        contributing_factors.append(f"Baseline category weight ({incident_type}): +{base_weight}")

        # Consciousness
        if consciousness == "UNRESPONSIVE":
            score += 40
            contributing_factors.append("Unresponsive consciousness: +40")
        elif consciousness == "DROWSY":
            score += 25
            contributing_factors.append("Drowsy / altered consciousness: +25")

        # Respiration
        if breathing == "DIFFICULT":
            score += 35
            contributing_factors.append("Severe respiratory struggle: +35")

        # Hemorrhage
        if bleeding == "MODERATE":
            score += 15
            contributing_factors.append("Moderate bleeding: +15")

        # Trapped victim
        trapped = answer_map.get("Q_RTA_TRAPPED")
        if trapped == "YES":
            score += 25
            contributing_factors.append("Casualty mechanically trapped: +25")

        # Cyanosis
        cyanosis = answer_map.get("Q_RESP_CYANOSIS")
        if cyanosis == "YES":
            score += 35
            contributing_factors.append("Severe cyanosis / hypoxia: +35")

        # Radiating cardiac pain
        cardiac_rad = answer_map.get("Q_CARDIAC_RADIATION")
        if cardiac_rad == "YES":
            score += 25
            contributing_factors.append("Radiating chest pain with diaphoresis: +25")

        # Stroke FAST
        fast_signs = answer_map.get("Q_FAST_SIGNS")
        if fast_signs and fast_signs != "NONE":
            score += 25
            contributing_factors.append(f"Acute neurological stroke symptoms ({fast_signs}): +25")

        # Multi-Casualty adjustment
        if reported_casualties >= 5:
            score += 20
            contributing_factors.append(f"Mass casualty incident ({reported_casualties} injured): +20")
        elif reported_casualties > 1:
            score += 10
            contributing_factors.append(f"Multiple casualties ({reported_casualties} injured): +10")

        # Hazards
        for h in hazards:
            if h in ["VEHICLE_FIRE", "HIGH_VOLTAGE"]:
                score += 20
                contributing_factors.append(f"Extreme hazard ({h}): +20")
            elif h == "FUEL_LEAK":
                score += 10
                contributing_factors.append(f"Hazard ({h}): +10")

        # Cap score between 0 and 100
        urgency_score = min(100, max(0, score))

        # Assign Tier
        if urgency_score >= 80:
            tier = PriorityTier.P1_CRITICAL
        elif urgency_score >= 45:
            tier = PriorityTier.P2_HIGH_URGENCY
        else:
            tier = PriorityTier.P3_LOWER_URGENCY

        return (
            tier,
            urgency_score,
            False,
            None,
            contributing_factors
        )

priority_engine = PriorityEngine()
