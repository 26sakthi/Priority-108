import React, { useState } from 'react';
import type { Recommendation, IncidentSummary } from '../api/client';

interface RecommendationCardProps {
  incident: IncidentSummary | null;
  recommendations: Recommendation[];
  onConfirmDispatch: (rec: Recommendation) => void;
  onOpenOverride: (rec: Recommendation) => void;
  isLoading: boolean;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  incident,
  recommendations,
  onConfirmDispatch,
  onOpenOverride,
  isLoading
}) => {
  const [selectedRank, setSelectedRank] = useState<number>(1);

  if (!incident) {
    return (
      <div className="glass-panel" style={{
        padding: '30px',
        textAlign: 'center',
        color: 'var(--text-dim)',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '13px'
      }}>
        Select an active incident from the queue to review AI dispatch proposals.
      </div>
    );
  }

  const activeRec = recommendations.find(r => r.rank === selectedRank) || recommendations[0];

  return (
    <div className="glass-panel" style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      overflow: 'hidden'
    }}>
      {/* Dossier Header */}
      <div style={{
        padding: '14px 18px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'rgba(0, 0, 0, 0.2)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-cyan)' }}>
              INCIDENT DOSSIER
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: '#94a3b8' }}>
              {incident.incident_number}
            </span>
          </div>
          <h2 style={{ fontSize: '15px', fontWeight: 700, margin: '2px 0 0 0', color: '#fff' }}>
            {incident.incident_type.replace(/_/g, ' ')}
          </h2>
        </div>

        <div style={{ textAlign: 'right' }}>
          <span style={{
            fontSize: '11px',
            fontWeight: 800,
            padding: '3px 8px',
            borderRadius: '4px',
            background: incident.priority_tier === 'P1_CRITICAL' ? 'var(--p1-red-bg)' : 'var(--p2-amber-bg)',
            color: incident.priority_tier === 'P1_CRITICAL' ? 'var(--p1-red)' : 'var(--p2-amber)',
            border: `1px solid ${incident.priority_tier === 'P1_CRITICAL' ? 'var(--p1-red-border)' : 'var(--p2-amber-border)'}`
          }}>
            {incident.priority_tier} ({incident.urgency_score} pts)
          </span>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Status: <strong style={{ color: '#e2e8f0' }}>{incident.status}</strong>
          </div>
        </div>
      </div>

      {/* Ranks Switcher */}
      {recommendations.length > 0 && (
        <div style={{
          display: 'flex',
          padding: '8px 16px',
          gap: '8px',
          borderBottom: '1px solid var(--border-subtle)',
          background: 'rgba(255, 255, 255, 0.02)'
        }}>
          {recommendations.map(r => (
            <button
              key={r.rank}
              onClick={() => setSelectedRank(r.rank)}
              style={{
                flex: 1,
                padding: '6px 10px',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: 700,
                cursor: 'pointer',
                background: selectedRank === r.rank ? 'var(--accent-cyan)' : 'rgba(255,255,255,0.05)',
                color: selectedRank === r.rank ? '#000' : 'var(--text-muted)',
                border: selectedRank === r.rank ? 'none' : '1px solid var(--border-subtle)'
              }}
            >
              Proposal #{r.rank} ({r.ambulance.vehicle_code} • {Math.round(r.suitability_score * 100)}%)
            </button>
          ))}
        </div>
      )}

      {/* Body Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
        {isLoading && (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            Calculating Dijkstra shortest paths & capability matching...
          </div>
        )}

        {!isLoading && !activeRec && (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
            No recommendations generated yet.
          </div>
        )}

        {!isLoading && activeRec && (
          <div>
            {/* Rationale Explanation Box */}
            <div style={{
              padding: '12px 14px',
              borderRadius: '8px',
              background: 'rgba(6, 182, 212, 0.1)',
              border: '1px solid rgba(6, 182, 212, 0.3)',
              marginBottom: '16px'
            }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
                🧠 AI Dispatcher Copilot Rationale:
              </span>
              <p style={{ fontSize: '12px', color: '#e2e8f0', margin: '4px 0 0 0', lineHeight: 1.4 }}>
                {activeRec.recommendation_rationale}
              </p>
            </div>

            {/* Grid 2 Columns: Ambulance Unit vs Receiving Hospital */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '16px' }}>
              {/* Ambulance Card */}
              <div style={{
                padding: '14px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--border-subtle)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)' }}>
                    RECOMMENDED AMBULANCE
                  </span>
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 800,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: activeRec.ambulance.ambulance_type === 'ALS' ? 'rgba(6, 182, 212, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                    color: activeRec.ambulance.ambulance_type === 'ALS' ? '#38bdf8' : '#34d399'
                  }}>
                    {activeRec.ambulance.ambulance_type}
                  </span>
                </div>

                <div style={{ fontSize: '15px', fontWeight: 800, color: '#fff', marginBottom: '2px' }}>
                  {activeRec.ambulance.vehicle_code}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginBottom: '10px' }}>
                  Base: {activeRec.ambulance.base_station}
                </div>

                {/* ETA to Scene */}
                <div style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: '6px',
                  marginBottom: '10px'
                }}>
                  <span style={{ fontSize: '20px', fontFamily: 'var(--font-mono)', fontWeight: 800, color: '#f8fafc' }}>
                    {Math.round(activeRec.eta_to_scene_seconds / 60)} min
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    ({(activeRec.distance_to_scene_meters / 1000).toFixed(1)} km to scene)
                  </span>
                </div>

                {/* Onboard Kit tags */}
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                  {activeRec.ambulance.equipment.map((eq, i) => (
                    <span key={i} style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: 'rgba(255, 255, 255, 0.06)',
                      color: '#cbd5e1'
                    }}>
                      ✓ {eq.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>

              {/* Hospital Card */}
              <div style={{
                padding: '14px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--border-subtle)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)' }}>
                    RECEIVING HOSPITAL
                  </span>
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: activeRec.receiving_hospital.icu_beds_available > 0 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                    color: activeRec.receiving_hospital.icu_beds_available > 0 ? '#34d399' : '#fca5a5'
                  }}>
                    {activeRec.receiving_hospital.icu_beds_available} ICU Beds Open
                  </span>
                </div>

                <div style={{ fontSize: '14px', fontWeight: 800, color: '#fff', marginBottom: '2px' }}>
                  {activeRec.receiving_hospital.name}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginBottom: '10px' }}>
                  Trauma Gate: {activeRec.receiving_hospital.contact_phone || '+91 108 Emergency'}
                </div>

                {/* Hospital Transit Time */}
                <div style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: '6px',
                  marginBottom: '10px'
                }}>
                  <span style={{ fontSize: '20px', fontFamily: 'var(--font-mono)', fontWeight: 800, color: '#f8fafc' }}>
                    {Math.round((activeRec.receiving_hospital.eta_to_hospital_seconds || 600) / 60)} min
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    ({((activeRec.receiving_hospital.distance_to_hospital_meters || 5000) / 1000).toFixed(1)} km from scene)
                  </span>
                </div>

                {/* Specialties */}
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                  {activeRec.receiving_hospital.specialties.map((s, i) => (
                    <span key={i} style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: 'rgba(139, 92, 246, 0.2)',
                      color: '#c4b5fd'
                    }}>
                      🏥 {s.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Suitability Match Gauge */}
            <div style={{
              padding: '12px 16px',
              borderRadius: '8px',
              background: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid var(--border-subtle)',
              marginBottom: '18px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  AI Recommendation Score
                </span>
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0', marginTop: '2px' }}>
                  Capability + Travel Time + Bed Availability
                </div>
              </div>
              <div style={{
                fontSize: '24px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 800,
                color: 'var(--accent-cyan)'
              }}>
                {Math.round(activeRec.suitability_score * 100)}%
              </div>
            </div>

            {/* Decision Confirmation Controls */}
            {incident.status !== 'DISPATCHED' ? (
              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  type="button"
                  onClick={() => onOpenOverride(activeRec)}
                  style={{
                    flex: 1,
                    padding: '12px',
                    borderRadius: '8px',
                    background: 'transparent',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    color: 'var(--text-muted)',
                    fontSize: '13px',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Override Proposal
                </button>

                <button
                  type="button"
                  onClick={() => onConfirmDispatch(activeRec)}
                  style={{
                    flex: 2,
                    padding: '12px',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, #10b981, #059669)',
                    border: 'none',
                    color: '#fff',
                    fontSize: '13px',
                    fontWeight: 800,
                    cursor: 'pointer',
                    boxShadow: '0 4px 15px rgba(16, 185, 129, 0.35)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px'
                  }}
                >
                  <span>✓</span>
                  <span>CONFIRM DISPATCH &amp; ROUTE</span>
                </button>
              </div>
            ) : (
              <div style={{
                textAlign: 'center',
                padding: '12px',
                borderRadius: '8px',
                background: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid rgba(16, 185, 129, 0.4)',
                color: '#34d399',
                fontSize: '13px',
                fontWeight: 700
              }}>
                ✓ Vehicle {incident.assigned_ambulance?.vehicle_code || 'En Route'} Dispatched to Scene
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
