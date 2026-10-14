import React, { useState } from 'react';
import type { IncidentSummary } from '../api/client';

interface IncidentQueueProps {
  incidents: IncidentSummary[];
  selectedId: string | null;
  onSelect: (incident: IncidentSummary) => void;
  isLoading: boolean;
}

export const IncidentQueue: React.FC<IncidentQueueProps> = ({
  incidents,
  selectedId,
  onSelect,
  isLoading
}) => {
  const [filterType, setFilterType] = useState<string>('ALL');

  const filtered = incidents.filter(inc => {
    if (filterType === 'ALL') return true;
    return inc.priority_tier === filterType;
  });

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'P1_CRITICAL':
        return {
          label: 'P1 CRITICAL',
          bg: 'var(--p1-red-bg)',
          color: 'var(--p1-red)',
          border: 'var(--p1-red-border)',
          pulse: true
        };
      case 'P2_HIGH_URGENCY':
        return {
          label: 'P2 HIGH',
          bg: 'var(--p2-amber-bg)',
          color: 'var(--p2-amber)',
          border: 'var(--p2-amber-border)',
          pulse: false
        };
      default:
        return {
          label: 'P3 LOWER',
          bg: 'var(--p3-blue-bg)',
          color: 'var(--p3-blue)',
          border: 'var(--p3-blue-border)',
          pulse: false
        };
    }
  };

  return (
    <div className="glass-panel" style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      overflow: 'hidden'
    }}>
      {/* Pane Header */}
      <div style={{
        padding: '14px 16px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div>
          <h2 style={{ fontSize: '14px', fontWeight: 700, letterSpacing: '0.5px', textTransform: 'uppercase' }}>
            Live Priority Queue
          </h2>
          <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
            Sorted by Urgency (P1 &gt; P2 &gt; P3)
          </span>
        </div>
        <span style={{
          fontSize: '11px',
          fontWeight: 700,
          background: 'rgba(255, 255, 255, 0.08)',
          padding: '2px 8px',
          borderRadius: '12px'
        }}>
          {filtered.length} INCIDENTS
        </span>
      </div>

      {/* Filter Tabs */}
      <div style={{
        display: 'flex',
        padding: '8px 12px',
        gap: '6px',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(0, 0, 0, 0.2)'
      }}>
        {['ALL', 'P1_CRITICAL', 'P2_HIGH_URGENCY', 'P3_LOWER_URGENCY'].map((f) => (
          <button
            key={f}
            onClick={() => setFilterType(f)}
            style={{
              flex: 1,
              padding: '5px 0',
              fontSize: '11px',
              fontWeight: 600,
              background: filterType === f ? 'rgba(255,255,255,0.12)' : 'transparent',
              color: filterType === f ? '#fff' : 'var(--text-muted)',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            {f === 'ALL' ? 'ALL' : f.split('_')[0]}
          </button>
        ))}
      </div>

      {/* Queue List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '10px' }}>
        {isLoading && (
          <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)', fontSize: '13px' }}>
            Updating active queue...
          </div>
        )}

        {!isLoading && filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-dim)', fontSize: '13px' }}>
            No active emergencies matching filter.
          </div>
        )}

        {filtered.map((inc) => {
          const badge = getTierBadge(inc.priority_tier);
          const isSelected = inc.incident_id === selectedId;

          return (
            <div
              key={inc.incident_id}
              onClick={() => onSelect(inc)}
              style={{
                padding: '12px',
                marginBottom: '8px',
                borderRadius: '10px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                background: isSelected ? 'rgba(6, 182, 212, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                border: isSelected
                  ? '1px solid rgba(6, 182, 212, 0.6)'
                  : `1px solid ${inc.priority_tier === 'P1_CRITICAL' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(255, 255, 255, 0.06)'}`,
                boxShadow: isSelected ? '0 0 15px rgba(6, 182, 212, 0.2)' : 'none'
              }}
            >
              {/* Top row: Number, Badge, Score */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 600, color: '#e2e8f0' }}>
                  {inc.incident_number}
                </span>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{
                    fontSize: '10px',
                    fontWeight: 700,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: badge.bg,
                    color: badge.color,
                    border: `1px solid ${badge.border}`
                  }}>
                    {badge.label}
                  </span>
                  <span style={{
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    color: inc.urgency_score >= 80 ? 'var(--p1-red)' : '#38bdf8'
                  }}>
                    {inc.urgency_score} pts
                  </span>
                </div>
              </div>

              {/* Type and Landmark */}
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc', marginBottom: '4px' }}>
                {inc.incident_type.replace(/_/g, ' ')}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                📍 {inc.address_landmark}
              </div>

              {/* Meta tags: Casualties, Calls, Status */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px' }}>
                <span style={{
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: inc.affected_casualty_count > 1 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                  color: inc.affected_casualty_count > 1 ? '#fca5a5' : 'var(--text-dim)',
                  fontWeight: 600
                }}>
                  👥 {inc.affected_casualty_count} Injured
                </span>

                <span style={{
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  color: 'var(--text-dim)'
                }}>
                  📞 {inc.call_count} {inc.call_count === 1 ? 'call' : 'calls'}
                </span>

                <span style={{
                  marginLeft: 'auto',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '10px',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: inc.status === 'DISPATCHED' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255,255,255,0.06)',
                  color: inc.status === 'DISPATCHED' ? '#34d399' : 'var(--text-muted)'
                }}>
                  {inc.status}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
