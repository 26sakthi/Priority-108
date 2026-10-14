import React, { useState } from 'react';
import type { Recommendation } from '../api/client';

interface OverrideModalProps {
  isOpen: boolean;
  recommendation: Recommendation | null;
  onClose: () => void;
  onSubmitOverride: (reason: string) => void;
}

export const OverrideModal: React.FC<OverrideModalProps> = ({
  isOpen,
  recommendation,
  onClose,
  onSubmitOverride
}) => {
  const [reason, setReason] = useState<string>('Paramedic crew requested alternative staging location');

  if (!isOpen || !recommendation) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ padding: '24px' }}>
        <h2 style={{ fontSize: '17px', fontWeight: 700, margin: '0 0 8px 0', color: '#fff' }}>
          Manual Operator Override
        </h2>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '0 0 16px 0' }}>
          In safety-critical 112/108 dispatch, human operators possess final authority. An immutable audit record will log this override.
        </p>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#f8fafc', marginBottom: '6px' }}>
            Override Reason Code / Operational Justification:
          </label>
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              color: '#fff',
              fontSize: '13px',
              marginBottom: '10px'
            }}
          >
            <option value="Paramedic crew requested alternative staging location">Paramedic crew requested alternative staging location</option>
            <option value="Hospital ER reported sudden diversion / critical trauma influx">Hospital ER reported sudden diversion / trauma influx</option>
            <option value="Local police / fire chief on-scene requested immediate alternate unit">Local police / fire chief on-scene requested alternate unit</option>
            <option value="Severe road closure / bridge construction reported by traffic police">Severe road closure / construction detour reported</option>
            <option value="Other clinical judgment">Other clinical judgment</option>
          </select>

          <textarea
            rows={3}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Type specific rationale..."
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              color: '#fff',
              fontSize: '13px',
              resize: 'vertical'
            }}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: '9px 16px',
              borderRadius: '8px',
              background: 'transparent',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-muted)',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>

          <button
            type="button"
            onClick={() => onSubmitOverride(reason)}
            style={{
              padding: '9px 20px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #f59e0b, #d97706)',
              border: 'none',
              color: '#000',
              fontWeight: 800,
              fontSize: '13px',
              cursor: 'pointer'
            }}
          >
            Log Override &amp; Confirm Dispatch ✍️
          </button>
        </div>
      </div>
    </div>
  );
};
