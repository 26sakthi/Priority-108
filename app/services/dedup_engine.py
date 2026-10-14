import math
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from app.schemas.domain import MatchConfidence, PriorityTier
from app.models.models import Incident
from app.core.config import settings

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two GPS points in meters.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

class DedupEngine:
    def __init__(
        self,
        max_radius_meters: float = settings.DEDUP_RADIUS_METERS,
        max_time_seconds: int = settings.DEDUP_TIME_WINDOW_SECONDS
    ):
        self.max_radius = max_radius_meters
        self.max_time_window = max_time_seconds

    def check_duplicate(
        self,
        latitude: float,
        longitude: float,
        incident_type: str,
        active_incidents: List[Incident],
        landmark: Optional[str] = None,
        reported_casualties: int = 1
    ) -> Tuple[MatchConfidence, float, Optional[Incident], Optional[Dict[str, Any]]]:
        """
        Evaluates an incoming call against all active incidents.
        Returns:
            (match_confidence, confidence_score, matched_incident, details_dict)
        """
        now = datetime.utcnow()
        best_match: Optional[Incident] = None
        highest_score = 0.0
        best_details: Optional[Dict[str, Any]] = None

        for inc in active_incidents:
            dist = haversine_distance(latitude, longitude, inc.latitude, inc.longitude)
            if dist > self.max_radius:
                continue

            # Time gap calculation
            time_gap = (now - inc.created_at).total_seconds()
            if time_gap < 0:
                time_gap = 0
            if time_gap > self.max_time_window:
                continue

            # Distance sub-score (0.0 to 1.0)
            dist_score = max(0.0, 1.0 - (dist / self.max_radius))

            # Time sub-score (0.0 to 1.0)
            time_score = max(0.0, 1.0 - (time_gap / self.max_time_window))

            # Incident Type sub-score
            type_score = 1.0 if inc.incident_type == incident_type else 0.4

            # Landmark token overlap sub-score
            landmark_score = 0.5
            if landmark and inc.address_landmark:
                l1_words = set(landmark.lower().split())
                l2_words = set(inc.address_landmark.lower().split())
                common = l1_words.intersection(l2_words)
                if common:
                    landmark_score = min(1.0, 0.6 + 0.1 * len(common))

            # Weighted composite similarity
            composite_score = (
                0.50 * dist_score
                + 0.25 * time_score
                + 0.15 * type_score
                + 0.10 * landmark_score
            )

            if composite_score > highest_score:
                highest_score = composite_score
                best_match = inc
                best_details = {
                    "distance_meters": int(dist),
                    "time_gap_seconds": int(time_gap),
                    "current_casualty_count": inc.affected_casualty_count,
                    "projected_new_casualty_count": max(inc.affected_casualty_count, reported_casualties),
                    "current_priority_tier": inc.priority_tier
                }

        highest_score = round(highest_score, 2)

        if highest_score >= 0.85 and best_match:
            return (MatchConfidence.HIGH_MATCH, highest_score, best_match, best_details)
        elif highest_score >= 0.50 and best_match:
            return (MatchConfidence.UNCERTAIN_MATCH, highest_score, best_match, best_details)
        else:
            return (MatchConfidence.NO_MATCH, highest_score, None, None)

dedup_engine = DedupEngine()
