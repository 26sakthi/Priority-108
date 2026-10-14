import uuid
from typing import List, Dict, Any, Optional
from app.models.models import Ambulance, Hospital, Incident, DispatchRecommendation
from app.services.routing_engine import routing_engine
from app.schemas.api_payloads import (
    RecommendationItem, AmbulanceInfo, HospitalInfo, GeoRouteGeometry
)
from app.schemas.domain import PriorityTier, AmbulanceType, AmbulanceStatus

class AllocationEngine:
    def rank_recommendations(
        self,
        incident: Incident,
        ambulances: List[Ambulance],
        hospitals: List[Hospital]
    ) -> List[RecommendationItem]:
        """
        Generates top 3 capability-aware ambulance + hospital recommendations.
        """
        # 1. Filter ambulances by operational status
        available_ambulances = [
            a for a in ambulances if a.status == "AVAILABLE"
        ]
        if not available_ambulances:
            # Fallback to non-maintenance if none marked strictly AVAILABLE
            available_ambulances = [
                a for a in ambulances if a.status != "MAINTENANCE"
            ]

        # 2. Capability filter
        tier = incident.priority_tier
        is_p1 = (tier == PriorityTier.P1_CRITICAL.value or tier == "P1_CRITICAL")
        
        als_units = [a for a in available_ambulances if a.ambulance_type == "ALS"]
        bls_units = [a for a in available_ambulances if a.ambulance_type == "BLS"]
        pts_units = [a for a in available_ambulances if a.ambulance_type == "PTS"]

        # Prioritize unit pool based on tier
        if is_p1:
            candidate_pool = als_units if als_units else (bls_units + pts_units)
            downgrade_notice = " [BLS Downgrade: No ALS available]" if not als_units else ""
        elif tier in [PriorityTier.P2_HIGH_URGENCY.value, "P2_HIGH_URGENCY"]:
            candidate_pool = bls_units + als_units + pts_units
            downgrade_notice = ""
        else:
            candidate_pool = pts_units + bls_units + als_units
            downgrade_notice = ""

        # 3. Get best hospital for incident
        hospital_rankings = routing_engine.select_best_hospital_for_incident(
            incident.latitude, incident.longitude,
            incident.incident_type, tier, hospitals
        )
        if not hospital_rankings:
            # Emergency fallback: pick any hospital
            if hospitals:
                top_hosp = hospitals[0]
                h_dist, h_eta, h_route = routing_engine.calculate_dijkstra_route(
                    incident.latitude, incident.longitude, top_hosp.latitude, top_hosp.longitude
                )
                top_hospital_entry = (top_hosp, h_dist, h_eta, h_route, "Default receiving facility")
            else:
                return []
        else:
            top_hospital_entry = hospital_rankings[0]

        top_hosp, h_dist, h_eta, h_route, hosp_rationale = top_hospital_entry

        # 4. Rank candidate ambulances by ETA & equipment match
        scored_candidates = []
        for amb in candidate_pool:
            a_dist, a_eta, a_route = routing_engine.calculate_dijkstra_route(
                amb.latitude, amb.longitude, incident.latitude, incident.longitude
            )

            # Equipment score
            eq_set = set(amb.onboard_equipment or [])
            kit_score = 0.5
            if "VENTILATOR" in eq_set:
                kit_score += 0.25
            if "DEFIBRILLATOR" in eq_set:
                kit_score += 0.25

            # Crew score
            staff = amb.staff_qualifications or []
            crew_score = 0.8 if any("PARAMEDIC" in s for s in staff) else 0.5

            # ETA score (0 to 1, 0 if > 30 min)
            eta_score = max(0.0, 1.0 - (a_eta / 1800.0))

            # Composite match score
            suitability_score = round(
                (eta_score * 0.60) + (kit_score * 0.25) + (crew_score * 0.15),
                2
            )

            scored_candidates.append({
                "ambulance": amb,
                "distance_scene": a_dist,
                "eta_scene": a_eta,
                "scene_route": a_route,
                "suitability_score": suitability_score
            })

        # Sort by suitability score descending (highest suitability first)
        scored_candidates.sort(key=lambda x: x["suitability_score"], reverse=True)

        # 5. Format top 3 recommendations
        recommendations: List[RecommendationItem] = []
        for idx, item in enumerate(scored_candidates[:3], start=1):
            amb: Ambulance = item["ambulance"]
            
            # Formulate human-readable rationale
            type_label = amb.ambulance_type
            if is_p1 and type_label == "ALS":
                match_desc = "ALS Unit matched for P1 life-threat with onboard advanced life support"
            elif is_p1 and type_label != "ALS":
                match_desc = f"{type_label} unit deployed (Nearest available; ALS downgrade alert)"
            else:
                match_desc = f"{type_label} Unit matched for {incident.incident_type}"

            full_rationale = f"Rank {idx}: {match_desc}. Destination: {top_hosp.name} ({hosp_rationale}). ETA to scene: {int(item['eta_scene'] / 60)} min."

            recommendations.append(
                RecommendationItem(
                    recommendation_id=uuid.uuid4(),
                    rank=idx,
                    ambulance=AmbulanceInfo(
                        ambulance_id=uuid.UUID(amb.ambulance_id),
                        vehicle_code=amb.vehicle_code,
                        ambulance_type=AmbulanceType(amb.ambulance_type),
                        status=AmbulanceStatus(amb.status),
                        latitude=amb.latitude,
                        longitude=amb.longitude,
                        base_station=amb.base_station_name,
                        staff=amb.staff_qualifications or [],
                        equipment=amb.onboard_equipment or []
                    ),
                    eta_to_scene_seconds=item["eta_scene"],
                    distance_to_scene_meters=item["distance_scene"],
                    receiving_hospital=HospitalInfo(
                        hospital_id=uuid.UUID(top_hosp.hospital_id),
                        name=top_hosp.name,
                        latitude=top_hosp.latitude,
                        longitude=top_hosp.longitude,
                        specialties=top_hosp.specialties or [],
                        icu_beds_available=top_hosp.icu_beds_available,
                        general_beds_available=top_hosp.general_beds_available,
                        is_accepting_emergencies=top_hosp.is_accepting_emergencies,
                        contact_phone=top_hosp.contact_phone,
                        eta_to_hospital_seconds=h_eta,
                        distance_to_hospital_meters=h_dist,
                        specialty_matched=hosp_rationale
                    ),
                    suitability_score=item["suitability_score"],
                    recommendation_rationale=full_rationale,
                    scene_route=GeoRouteGeometry(coordinates=item["scene_route"]),
                    hospital_route=GeoRouteGeometry(coordinates=h_route)
                )
            )

        return recommendations

allocation_engine = AllocationEngine()
