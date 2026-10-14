from typing import List, Optional, Tuple, Any
from app.schemas.allocation import AmbulanceType, PriorityTier
from app.services.routing_estimator import compute_estimated_travel_time

class CandidateEvaluation:
    def __init__(
        self,
        ambulance: Any,
        est_seconds: int,
        distance_meters: int,
        is_exact_match: bool,
        is_downgrade: bool
    ):
        self.ambulance = ambulance
        self.est_seconds = est_seconds
        self.distance_meters = distance_meters
        self.is_exact_match = is_exact_match
        self.is_downgrade = is_downgrade

def select_best_ambulance(
    ambulances: List[Any],
    patient_lat: float,
    patient_lon: float,
    required_capability: AmbulanceType,
    priority_tier: PriorityTier,
    max_acceptable_est_seconds: int = 1800
) -> Tuple[Optional[Any], Optional[int], Optional[int], str, bool]:
    """
    Pure, deterministic selection engine for automatic ambulance allocation.
    
    Returns:
        (selected_ambulance, est_travel_seconds, distance_meters, rationale, is_capability_downgrade)
    """
    # 1. Filter by operational availability
    available_units = [a for a in ambulances if getattr(a, "status", None) == "AVAILABLE"]
    if not available_units:
        return (
            None,
            None,
            None,
            "All ambulance units in sector are currently committed or offline. Incident queued for next available vehicle.",
            False
        )

    # 2. Capability matching & tiered fallback policy
    eligible_evaluations: List[CandidateEvaluation] = []

    if required_capability == AmbulanceType.ALS:
        # Ideal: ALS units
        als_units = [a for a in available_units if getattr(a, "ambulance_type", None) == AmbulanceType.ALS.value]
        if als_units:
            for amb in als_units:
                est, dist, _ = compute_estimated_travel_time(amb.latitude, amb.longitude, patient_lat, patient_lon)
                if est <= max_acceptable_est_seconds:
                    eligible_evaluations.append(CandidateEvaluation(amb, est, dist, is_exact_match=True, is_downgrade=False))
        elif priority_tier == PriorityTier.P1_CRITICAL:
            # Policy Fallback for P1: Zero ALS available, fall back to closest BLS for immediate on-scene CPR/stabilization
            bls_units = [a for a in available_units if getattr(a, "ambulance_type", None) == AmbulanceType.BLS.value]
            for amb in bls_units:
                est, dist, _ = compute_estimated_travel_time(amb.latitude, amb.longitude, patient_lat, patient_lon)
                if est <= max_acceptable_est_seconds:
                    eligible_evaluations.append(CandidateEvaluation(amb, est, dist, is_exact_match=False, is_downgrade=True))
    else:
        # Required is BLS
        # Ideal: BLS units (conserve ALS for potential P1 emergencies)
        bls_units = [a for a in available_units if getattr(a, "ambulance_type", None) == AmbulanceType.BLS.value]
        if bls_units:
            for amb in bls_units:
                est, dist, _ = compute_estimated_travel_time(amb.latitude, amb.longitude, patient_lat, patient_lon)
                if est <= max_acceptable_est_seconds:
                    eligible_evaluations.append(CandidateEvaluation(amb, est, dist, is_exact_match=True, is_downgrade=False))
        else:
            # Up-tier fallback: No BLS available, use available ALS
            als_units = [a for a in available_units if getattr(a, "ambulance_type", None) == AmbulanceType.ALS.value]
            for amb in als_units:
                est, dist, _ = compute_estimated_travel_time(amb.latitude, amb.longitude, patient_lat, patient_lon)
                if est <= max_acceptable_est_seconds:
                    eligible_evaluations.append(CandidateEvaluation(amb, est, dist, is_exact_match=False, is_downgrade=False))

    # 3. Check if any candidate satisfied distance & threshold constraints
    if not eligible_evaluations:
        return (
            None,
            None,
            None,
            f"No available {required_capability.value} units within maximum acceptable response window ({max_acceptable_est_seconds // 60}m). Emergency queued.",
            False
        )

    # 4. Deterministic Ranking & Tie-Breaking
    # Key 1: Shortest travel time (est_seconds)
    # Key 2: Exact capability match preferred over cross-tier fallback
    # Key 3: Lexicographical vehicle_code for strictly reproducible sorting
    eligible_evaluations.sort(
        key=lambda cand: (
            cand.est_seconds,
            not cand.is_exact_match,
            getattr(cand.ambulance, "vehicle_code", "")
        )
    )

    winner = eligible_evaluations[0]
    amb = winner.ambulance
    minutes = winner.est_seconds // 60
    seconds = winner.est_seconds % 60

    if winner.is_downgrade:
        rationale = (
            f"DOWNGRADE DISPATCH: No ALS units available for P1 incident. "
            f"Auto-assigned nearest available BLS unit ({amb.vehicle_code}, EST: {minutes}m {seconds}s) for rapid on-scene stabilization."
        )
    else:
        rationale = (
            f"Auto-assigned nearest available {amb.ambulance_type} unit ({amb.vehicle_code}, EST: {minutes}m {seconds}s) "
            f"matching {priority_tier.value} / {required_capability.value} requirements."
        )

    return (amb, winner.est_seconds, winner.distance_meters, rationale, winner.is_downgrade)
