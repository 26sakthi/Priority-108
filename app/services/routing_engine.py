import networkx as nx
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
from app.services.dedup_engine import haversine_distance
from app.models.models import Hospital
from app.core.config import settings

# Perambalur / Trichy Sector Key Nodes (Lat, Lon, Label)
REGIONAL_NODES = {
    "N_NH45_PERAMBALUR_NORTH": (11.254123, 78.894123),
    "N_DS_HOSPITAL_GATE": (11.244123, 78.884123),
    "N_PERAMBALUR_OLD_BUS_STAND": (11.234123, 78.874123),
    "N_GOVT_HOSPITAL_PERAMBALUR": (11.231123, 78.871123),
    "N_NH45_SAMAYAPURAM_TOLL": (11.214123, 78.854123),
    "N_TRICHY_NORTH_BYPASS": (10.914123, 78.714123),
    "N_TRICHY_MED_COLLEGE": (10.834123, 78.694123),
    "N_MANACHANALLUR_JUNCTION": (10.904123, 78.684123),
    "N_ARIYALUR_ROAD_FORK": (11.240000, 78.880000),
    "N_THURAIYUR_CROSSING": (11.220000, 78.860000)
}

# Road Segments (u, v, speed_kmh, label)
REGIONAL_EDGES = [
    ("N_NH45_PERAMBALUR_NORTH", "N_DS_HOSPITAL_GATE", 60.0, "NH-45 Highway Section 1"),
    ("N_DS_HOSPITAL_GATE", "N_ARIYALUR_ROAD_FORK", 50.0, "Medical College Access Boulevard"),
    ("N_ARIYALUR_ROAD_FORK", "N_PERAMBALUR_OLD_BUS_STAND", 40.0, "Town Arterial Road"),
    ("N_PERAMBALUR_OLD_BUS_STAND", "N_GOVT_HOSPITAL_PERAMBALUR", 35.0, "Hospital Link Road"),
    ("N_PERAMBALUR_OLD_BUS_STAND", "N_THURAIYUR_CROSSING", 50.0, "South Arterial Link"),
    ("N_THURAIYUR_CROSSING", "N_NH45_SAMAYAPURAM_TOLL", 70.0, "NH-45 Express Link"),
    ("N_NH45_SAMAYAPURAM_TOLL", "N_TRICHY_NORTH_BYPASS", 80.0, "NH-45 Expressway South"),
    ("N_TRICHY_NORTH_BYPASS", "N_MANACHANALLUR_JUNCTION", 50.0, "Trichy Ring Road"),
    ("N_TRICHY_NORTH_BYPASS", "N_TRICHY_MED_COLLEGE", 45.0, "City Medical Corridor"),
    ("N_DS_HOSPITAL_GATE", "N_NH45_SAMAYAPURAM_TOLL", 65.0, "NH-45 Toll Access Bypass")
]

class RoutingEngine:
    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_road_graph()

    def _build_road_graph(self):
        # Add nodes with coordinates
        for node_id, (lat, lon) in REGIONAL_NODES.items():
            self.graph.add_node(node_id, lat=lat, lon=lon)

        # Add bidirectional edges
        for u, v, speed_kmh, label in REGIONAL_EDGES:
            u_lat, u_lon = REGIONAL_NODES[u]
            v_lat, v_lon = REGIONAL_NODES[v]
            dist_meters = haversine_distance(u_lat, u_lon, v_lat, v_lon)
            
            # Base duration in seconds = (dist / (speed * 1000/3600))
            base_duration = dist_meters / (speed_kmh * (1000.0 / 3600.0))

            # Add forward & backward directed edge
            self.graph.add_edge(
                u, v,
                distance=dist_meters,
                speed=speed_kmh,
                base_duration=base_duration,
                weight=base_duration,
                label=label
            )
            self.graph.add_edge(
                v, u,
                distance=dist_meters,
                speed=speed_kmh,
                base_duration=base_duration,
                weight=base_duration,
                label=label
            )

    def get_traffic_multiplier(self) -> float:
        """
        Calculates time-of-day traffic penalty multiplier:
        Peak hours (08:30-10:30, 17:30-19:30): 1.4x
        Off-peak hours: 1.0x
        """
        now = datetime.now()
        current_minute = now.hour * 60 + now.minute
        # Morning peak: 8:30 to 10:30 (510 to 630 min)
        # Evening peak: 17:30 to 19:30 (1050 to 1170 min)
        if (510 <= current_minute <= 630) or (1050 <= current_minute <= 1170):
            return settings.PEAK_HOURS_MULTIPLIER
        return 1.0

    def find_nearest_node(self, lat: float, lon: float) -> str:
        """Finds closest graph node to arbitrary coordinate."""
        closest_node = None
        min_dist = float("inf")
        for node_id, (n_lat, n_lon) in REGIONAL_NODES.items():
            d = haversine_distance(lat, lon, n_lat, n_lon)
            if d < min_dist:
                min_dist = d
                closest_node = node_id
        return closest_node

    def calculate_dijkstra_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float
    ) -> Tuple[int, int, List[List[float]]]:
        """
        Runs Dijkstra's algorithm over the OSM road graph.
        Returns:
            (distance_meters, duration_seconds, [[lon, lat], ...])
        """
        start_node = self.find_nearest_node(start_lat, start_lon)
        end_node = self.find_nearest_node(end_lat, end_lon)

        traffic_factor = self.get_traffic_multiplier()

        # Update dynamic weights with traffic
        for u, v, data in self.graph.edges(data=True):
            data["weight"] = data["base_duration"] * traffic_factor

        try:
            if start_node == end_node:
                # Direct route
                dist = int(haversine_distance(start_lat, start_lon, end_lat, end_lon) * settings.URBAN_DETOUR_FACTOR)
                duration = int(dist / (45.0 * 1000 / 3600) * traffic_factor)
                coords = [[start_lon, start_lat], [end_lon, end_lat]]
                return (dist, max(duration, 30), coords)

            path_nodes = nx.dijkstra_path(self.graph, start_node, end_node, weight="weight")
            
            # Compute total distance and duration along path
            total_dist = haversine_distance(start_lat, start_lon, REGIONAL_NODES[start_node][0], REGIONAL_NODES[start_node][1])
            total_duration = total_dist / (40.0 * 1000 / 3600) * traffic_factor
            
            coords = [[start_lon, start_lat]]
            for i in range(len(path_nodes) - 1):
                u = path_nodes[i]
                v = path_nodes[i + 1]
                edge_data = self.graph[u][v]
                total_dist += edge_data["distance"]
                total_duration += edge_data["weight"]
                coords.append([REGIONAL_NODES[u][1], REGIONAL_NODES[u][0]])

            last_node = path_nodes[-1]
            coords.append([REGIONAL_NODES[last_node][1], REGIONAL_NODES[last_node][0]])
            
            leg_to_end = haversine_distance(REGIONAL_NODES[last_node][0], REGIONAL_NODES[last_node][1], end_lat, end_lon)
            total_dist += leg_to_end
            total_duration += leg_to_end / (40.0 * 1000 / 3600) * traffic_factor
            coords.append([end_lon, end_lat])

            return (int(total_dist), int(total_duration), coords)

        except (nx.NetworkXNoPath, Exception):
            # Graceful Euclidean Haversine fallback with urban detour
            straight_dist = haversine_distance(start_lat, start_lon, end_lat, end_lon)
            detour_dist = int(straight_dist * settings.URBAN_DETOUR_FACTOR)
            detour_dur = int(detour_dist / (40.0 * 1000 / 3600) * traffic_factor)
            
            # Interpolate a 3-point geometry
            mid_lat = (start_lat + end_lat) / 2.0 + 0.002
            mid_lon = (start_lon + end_lon) / 2.0 + 0.002
            coords = [[start_lon, start_lat], [mid_lon, mid_lat], [end_lon, end_lat]]
            return (detour_dist, detour_dur, coords)

    def select_best_hospital_for_incident(
        self,
        incident_lat: float,
        incident_lon: float,
        incident_type: str,
        priority_tier: str,
        hospitals: List[Hospital]
    ) -> List[Tuple[Hospital, int, int, List[List[float]], str]]:
        """
        Filters and ranks hospitals based on Clinical Suitability + Open ICU Beds + Travel Time.
        Returns list of (hospital, distance_meters, eta_seconds, route_coords, rationale).
        """
        required_specialty = None
        if incident_type == "ROAD_TRAFFIC_ACCIDENT" and priority_tier == "P1_CRITICAL":
            required_specialty = "TRAUMA_LEVEL_1"
        elif incident_type == "CARDIAC_CHEST_PAIN":
            required_specialty = "CARDIAC_CATH_LAB"
        elif incident_type in ["STROKE_NEURO", "UNCONSCIOUS_FALL"] and priority_tier == "P1_CRITICAL":
            required_specialty = "NEUROLOGY"

        candidates = []
        for hosp in hospitals:
            if not hosp.is_accepting_emergencies:
                continue

            dist, eta, route = self.calculate_dijkstra_route(
                incident_lat, incident_lon, hosp.latitude, hosp.longitude
            )

            # Check specialty match
            hosp_specialties = hosp.specialties or []
            has_specialty = (required_specialty in hosp_specialties) if required_specialty else True
            has_icu = hosp.icu_beds_available > 0

            # Score: base is travel time, penalized if missing required capabilities
            suitability_penalty = 0
            rationale_parts = []
            
            if required_specialty:
                if has_specialty and has_icu:
                    rationale_parts.append(f"Matched {required_specialty} with {hosp.icu_beds_available} ICU beds available")
                elif has_specialty and not has_icu:
                    suitability_penalty += 900 # +15 min penalty for no ICU bed
                    rationale_parts.append(f"Has {required_specialty} but 0 ICU beds open")
                else:
                    suitability_penalty += 1800 # +30 min penalty for missing specialty
                    rationale_parts.append(f"Lacks required {required_specialty} facility")
            else:
                rationale_parts.append(f"General emergency ready ({hosp.general_beds_available} beds)")

            effective_score = eta + suitability_penalty
            rationale = "; ".join(rationale_parts)

            candidates.append((effective_score, hosp, dist, eta, route, rationale))

        # Sort by lowest effective score (combines clinical suitability and shortest path)
        candidates.sort(key=lambda x: x[0])

        return [(c[1], c[2], c[3], c[4], c[5]) for c in candidates]

routing_engine = RoutingEngine()
