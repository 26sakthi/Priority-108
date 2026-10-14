import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import type { AmbulanceFleet, HospitalFacility, IncidentSummary, Recommendation } from '../api/client';

interface MapViewProps {
  ambulances: AmbulanceFleet[];
  hospitals: HospitalFacility[];
  selectedIncident: IncidentSummary | null;
  activeRecommendation: Recommendation | null;
}

export const MapView: React.FC<MapViewProps> = ({
  ambulances,
  hospitals,
  selectedIncident,
  activeRecommendation
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      // Default center: Perambalur & Trichy sector (11.234123, 78.874123)
      const map = L.map(mapContainerRef.current, {
        center: [11.234123, 78.874123],
        zoom: 12,
        zoomControl: false
      });

      // Dark style tile layer from CartoDB Dark Matter
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 19
      }).addTo(map);

      L.control.zoom({ position: 'bottomright' }).addTo(map);

      layerGroupRef.current = L.layerGroup().addTo(map);
      mapInstanceRef.current = map;
    }

    return () => {
      // Map cleanup if unmounted
    };
  }, []);

  // Update Markers and Dijkstra Routes
  useEffect(() => {
    const map = mapInstanceRef.current;
    const layers = layerGroupRef.current;
    if (!map || !layers) return;

    layers.clearLayers();
    const boundsPoints: L.LatLngTuple[] = [];

    // 1. Ambulances Markers
    ambulances.forEach(amb => {
      const isALS = amb.ambulance_type === 'ALS';
      const icon = L.divIcon({
        className: 'custom-map-icon',
        html: `
          <div style="
            width: 28px; height: 28px; border-radius: 50%;
            background: ${isALS ? '#06b6d4' : '#10b981'};
            border: 2px solid #ffffff;
            color: #000; font-weight: 800; font-size: 10px;
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.6);
          ">
            ${isALS ? 'ALS' : 'BLS'}
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      });

      const marker = L.marker([amb.latitude, amb.longitude], { icon })
        .bindPopup(`
          <div style="padding: 4px;">
            <strong style="color: #38bdf8;">${amb.vehicle_code} (${amb.ambulance_type})</strong><br/>
            Status: <span style="color: #34d399;">${amb.status}</span><br/>
            Base: ${amb.base_station}
          </div>
        `);
      layers.addLayer(marker);
      boundsPoints.push([amb.latitude, amb.longitude]);
    });

    // 2. Hospitals Markers
    hospitals.forEach(hosp => {
      const icon = L.divIcon({
        className: 'custom-map-icon',
        html: `
          <div style="
            width: 32px; height: 32px; border-radius: 8px;
            background: #8b5cf6;
            border: 2px solid #ffffff;
            color: #fff; font-weight: 800; font-size: 14px;
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 4px 12px rgba(139, 92, 246, 0.5);
          ">
            🏥
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      });

      const marker = L.marker([hosp.latitude, hosp.longitude], { icon })
        .bindPopup(`
          <div style="padding: 4px;">
            <strong style="color: #c4b5fd;">${hosp.name}</strong><br/>
            ICU Beds: <span style="color: #34d399;">${hosp.icu_beds_available}</span><br/>
            Specialties: ${hosp.specialties.join(', ')}
          </div>
        `);
      layers.addLayer(marker);
      boundsPoints.push([hosp.latitude, hosp.longitude]);
    });

    // 3. Selected Incident Marker
    if (selectedIncident) {
      const isP1 = selectedIncident.priority_tier === 'P1_CRITICAL';
      const icon = L.divIcon({
        className: 'custom-map-icon',
        html: `
          <div style="
            width: 34px; height: 34px; border-radius: 50%;
            background: ${isP1 ? '#ef4444' : '#f59e0b'};
            border: 3px solid #ffffff;
            color: #fff; font-weight: 800; font-size: 16px;
            display: flex; align-items: center; justify-content: center;
            animation: pulse-red 1.2s infinite;
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.8);
          ">
            🚨
          </div>
        `,
        iconSize: [34, 34],
        iconAnchor: [17, 17]
      });

      const marker = L.marker([selectedIncident.latitude, selectedIncident.longitude], { icon })
        .bindPopup(`
          <div style="padding: 4px;">
            <strong style="color: #ef4444;">${selectedIncident.incident_number}</strong><br/>
            ${selectedIncident.incident_type}<br/>
            Priority: <strong>${selectedIncident.priority_tier}</strong><br/>
            Injured: ${selectedIncident.affected_casualty_count}
          </div>
        `);
      layers.addLayer(marker);
      boundsPoints.push([selectedIncident.latitude, selectedIncident.longitude]);
    }

    // 4. Render Dijkstra Route Lines from Active Recommendation
    if (activeRecommendation) {
      // Scene Route (Amber / Red Line: Ambulance -> Incident)
      if (activeRecommendation.scene_route && activeRecommendation.scene_route.coordinates) {
        const sceneCoords: L.LatLngTuple[] = activeRecommendation.scene_route.coordinates.map(
          c => [c[1], c[0]] // convert [lon, lat] to [lat, lon]
        );
        const scenePolyline = L.polyline(sceneCoords, {
          color: '#f59e0b',
          weight: 5,
          opacity: 0.9,
          dashArray: '8, 8',
          lineCap: 'round'
        }).bindPopup('Ambulance to Incident Scene Route');
        layers.addLayer(scenePolyline);
        sceneCoords.forEach(pt => boundsPoints.push(pt));
      }

      // Hospital Route (Cyan / Blue Line: Incident -> Hospital)
      if (activeRecommendation.hospital_route && activeRecommendation.hospital_route.coordinates) {
        const hospCoords: L.LatLngTuple[] = activeRecommendation.hospital_route.coordinates.map(
          c => [c[1], c[0]]
        );
        const hospPolyline = L.polyline(hospCoords, {
          color: '#06b6d4',
          weight: 5,
          opacity: 0.9,
          lineCap: 'round'
        }).bindPopup('Incident to Receiving Hospital Route');
        layers.addLayer(hospPolyline);
        hospCoords.forEach(pt => boundsPoints.push(pt));
      }
    }

    // Fit map bounds smoothly
    if (boundsPoints.length > 0) {
      try {
        map.fitBounds(L.latLngBounds(boundsPoints), { padding: [40, 40], maxZoom: 14 });
      } catch {
        // ignore bounds calculation error
      }
    }
  }, [ambulances, hospitals, selectedIncident, activeRecommendation]);

  return (
    <div className="glass-panel" style={{
      height: '100%',
      position: 'relative',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Map Header Overlay */}
      <div style={{
        position: 'absolute',
        top: '12px',
        left: '12px',
        zIndex: 500,
        background: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(8px)',
        padding: '6px 12px',
        borderRadius: '8px',
        border: '1px solid var(--border-subtle)',
        fontSize: '11px',
        fontWeight: 600,
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        color: '#e2e8f0'
      }}>
        <span>🗺️ Live OpenStreetMap GPS Telemetry</span>
        <span style={{ color: '#06b6d4' }}>● ALS Unit</span>
        <span style={{ color: '#10b981' }}>● BLS Unit</span>
        <span style={{ color: '#8b5cf6' }}>■ Hospital</span>
        <span style={{ color: '#f59e0b' }}>- - Scene Route</span>
        <span style={{ color: '#06b6d4' }}>── Hospital Route</span>
      </div>

      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};
