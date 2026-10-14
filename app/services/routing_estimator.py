import math
from typing import Tuple
from app.core.config import settings

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two geographic coordinates in meters.
    """
    R = 6371000.0  # Earth's mean radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def compute_estimated_travel_time(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    traffic_multiplier: float = 1.0
) -> Tuple[int, int, str]:
    """
    Estimates realistic road network travel time (EST) and distance.
    
    Distinguishes straight-line distance from actual road travel time:
    1. Base Euclidean / Haversine distance is calculated.
    2. Urban Detour Index (1.35x) accounts for street grid tortuosity.
    3. Emergency response vehicle speed (38 km/h) determines transit duration.
    4. Non-negative traffic multiplier modulates travel duration.
    
    Returns:
        (est_travel_seconds, distance_meters, method_label)
    """
    straight_line_m = haversine_distance_meters(origin_lat, origin_lon, dest_lat, dest_lon)
    
    # Apply calibrated urban tortuosity detour factor
    road_distance_m = int(straight_line_m * settings.URBAN_DETOUR_FACTOR)
    
    # Speed in meters per second
    speed_mps = (settings.AVERAGE_AMBULANCE_SPEED_KMH * 1000.0) / 3600.0
    
    # Calculate travel duration
    raw_seconds = (road_distance_m / speed_mps) * max(1.0, traffic_multiplier)
    est_seconds = int(math.ceil(raw_seconds))
    
    # Impose a minimum 30-second dispatch latency (turning out, intersection clearance)
    if est_seconds < 30 and straight_line_m > 10.0:
        est_seconds = 30
        
    return est_seconds, road_distance_m, "CALIBRATED_ROAD_DETOUR_MODEL"
