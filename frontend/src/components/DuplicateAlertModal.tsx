import React, { useState } from 'react';
import { api } from '../api/client';

interface DuplicateAlertModalProps {
  isOpen: boolean;
  dupInfo: any;
  newCallId: string;
  onClose: () => void;
  onMerged: (incidentId: string) => void;
}

export const DuplicateAlertModal: React.FC<DuplicateAlertModalProps> = ({
  isOpen,
  dupInfo,
  newCallId,
  onClose,
  onMerged
}) => {
  const [updatedCasualties, setUpdatedCasualties] = useState<number>(dupInfo?.projected_new_casualty_count || 2);
  const [notes, setNotes] = useState<string>('Second caller confirms additional trapped victims');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen || !dupInfo) return null;

  const handleMerge = async () => {
    setIsSubmitting(true);
    try {
      await api.mergeCall(dupInfo.incident_id, {
        call_id: newCallId,
        updated_casualty_count: updatedCasualties,
        additional_notes: notes
      });
      onMerged(dupInfo.incident_id);
      onClose();
    } catch (err) {
      alert('Error merging call: ' + err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '50%',
            background: 'rgba(245, 158, 11, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '22px'
          }}>
            ⚠️
          </div>
          <div>
            <h2 style={{ fontSize: '17px', fontWeight: 700, margin: 0, color: '#fbbf24' }}>
              Spatial Duplicate Call Detected
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
              Multi-factor matching identified an active incident within spatial &amp; temporal radius
            </p>
          </div>
        </div>

        {/* Comparison Details */}
        <div style={{
          padding: '14px',
          borderRadius: '10px',
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--border-subtle)',
          marginBottom: '16px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Target Active Incident:</span>
            <strong style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>{dupInfo.incident_number}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Separation Distance:</span>
            <strong style={{ color: '#fff' }}>{dupInfo.distance_meters} meters away</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Time Difference:</span>
            <strong style={{ color: '#fff' }}>{Math.round(dupInfo.time_gap_seconds / 60)} minutes apart</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Current Casualties:</span>
            <span style={{ color: '#fca5a5', fontWeight: 700 }}>
              {dupInfo.current_casualty_count} casualties recorded
            </span>
          </div>
        </div>

        {/* Casualty Invariant Input */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#f8fafc', marginBottom: '6px' }}>
            Update Cumulative Casualties Count:
          </label>
          <input
            type="number"
            min={dupInfo.current_casualty_count}
            value={updatedCasualties}
            onChange={(e) => setUpdatedCasualties(parseInt(e.target.value) || dupInfo.current_casualty_count)}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              color: '#fff',
              fontSize: '13px'
            }}
          />
          <span style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px', display: 'block' }}>
            * System enforces cumulative casualty preservation: count never decreases on duplicate merge.
          </span>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#f8fafc', marginBottom: '6px' }}>
            Additional Caller Details:
          </label>
          <input
            type="text"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              color: '#fff',
              fontSize: '13px'
            }}
          />
        </div>

        {/* Action Controls */}
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
            onClick={handleMerge}
            disabled={isSubmitting}
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
            {isSubmitting ? 'Merging...' : 'Merge Call & Consolidate 🔗'}
          </button>
        </div>
      </div>
    </div>
  );
};
