import React, { useState, useEffect } from 'react';

interface HeaderProps {
  onNewCall: () => void;
  trafficEnabled: boolean;
  onToggleTraffic: () => void;
  activeCount: number;
  p1Count: number;
}

export const Header: React.FC<HeaderProps> = ({
  onNewCall,
  trafficEnabled,
  onToggleTraffic,
  activeCount,
  p1Count
}) => {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString('en-IN', { hour12: false }) + ' UTC+05:30');
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '12px 24px',
      borderBottom: '1px solid var(--border-subtle)',
      background: 'rgba(10, 15, 29, 0.9)',
      backdropFilter: 'blur(10px)',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      {/* Brand & Sector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #06b6d4, #ef4444)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 800,
          fontSize: '20px',
          color: '#fff',
          boxShadow: '0 0 15px rgba(6, 182, 212, 0.5)'
        }}>
          P
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 style={{ fontSize: '18px', fontWeight: 700, letterSpacing: '-0.3px', margin: 0 }}>
              PriorityCare
            </h1>
            <span style={{
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
              padding: '2px 6px',
              borderRadius: '4px',
              background: 'rgba(6, 182, 212, 0.2)',
              color: '#38bdf8',
              border: '1px solid rgba(6, 182, 212, 0.3)'
            }}>
              112/108 COPILOT
            </span>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
            Sector: Perambalur & Trichy Central Emergency Command
          </p>
        </div>
      </div>

      {/* Center Telemetry & Pulse */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        {/* P1 Critical Counter */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 14px',
          borderRadius: '8px',
          background: p1Count > 0 ? 'var(--p1-red-bg)' : 'rgba(255, 255, 255, 0.04)',
          border: `1px solid ${p1Count > 0 ? 'var(--p1-red-border)' : 'var(--border-subtle)'}`
        }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: p1Count > 0 ? 'var(--p1-red)' : 'var(--text-dim)',
            animation: p1Count > 0 ? 'pulse-red 1.2s infinite' : 'none'
          }} />
          <span style={{ fontSize: '12px', fontWeight: 600, color: p1Count > 0 ? 'var(--p1-red)' : 'var(--text-muted)' }}>
            {p1Count} P1 CRITICAL
          </span>
        </div>

        {/* Total Active Incidents */}
        <div style={{
          padding: '6px 14px',
          borderRadius: '8px',
          background: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid var(--border-subtle)',
          fontSize: '12px',
          color: 'var(--text-muted)'
        }}>
          Active Queue: <strong style={{ color: '#fff' }}>{activeCount}</strong>
        </div>

        {/* Live Clock */}
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '13px',
          color: '#cbd5e1',
          background: '#040711',
          padding: '6px 12px',
          borderRadius: '6px',
          border: '1px solid rgba(255,255,255,0.06)'
        }}>
          {time}
        </div>
      </div>

      {/* Action Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Synthetic Traffic Toggle */}
        <button
          onClick={onToggleTraffic}
          title="Simulate Peak-Hour Road Congestion"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 14px',
            borderRadius: '8px',
            fontSize: '12px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            background: trafficEnabled ? 'rgba(245, 158, 11, 0.2)' : 'rgba(255, 255, 255, 0.05)',
            color: trafficEnabled ? '#fbbf24' : 'var(--text-muted)',
            border: `1px solid ${trafficEnabled ? 'rgba(245, 158, 11, 0.5)' : 'var(--border-subtle)'}`
          }}
        >
          <span>🚦 Traffic Surge:</span>
          <strong>{trafficEnabled ? 'PEAK (1.4x)' : 'OFF-PEAK'}</strong>
        </button>

        {/* New Call Button */}
        <button
          onClick={onNewCall}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 18px',
            borderRadius: '8px',
            fontSize: '13px',
            fontWeight: 700,
            cursor: 'pointer',
            background: 'linear-gradient(135deg, #06b6d4, #0284c7)',
            color: '#fff',
            border: 'none',
            boxShadow: '0 4px 15px rgba(6, 182, 212, 0.35)',
            transition: 'transform 0.15s ease'
          }}
          onMouseDown={(e) => (e.currentTarget.style.transform = 'scale(0.97)')}
          onMouseUp={(e) => (e.currentTarget.style.transform = 'scale(1)')}
        >
          <span style={{ fontSize: '16px' }}>📞</span>
          <span>NEW EMERGENCY CALL</span>
        </button>
      </div>
    </header>
  );
};
