import React, { useState } from 'react';
import { api } from '../api/client';
import type { Question } from '../api/client';

interface CallIntakeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onIntakeCompleted: (incidentId: string) => void;
  onDuplicateDetected: (dupInfo: any, newCallId: string) => void;
}

export const CallIntakeModal: React.FC<CallIntakeModalProps> = ({
  isOpen,
  onClose,
  onIntakeCompleted,
  onDuplicateDetected
}) => {
  // Step 1: Call Details
  const [phone, setPhone] = useState('+919876543210');
  const [callerName, setCallerName] = useState('Bystander');
  const [landmark, setLandmark] = useState('NH-45 Samayapuram Toll Plaza');
  const [incidentType, setIncidentType] = useState('ROAD_TRAFFIC_ACCIDENT');
  const [lat, setLat] = useState<number>(11.234123);
  const [lon, setLon] = useState<number>(78.874123);

  // Intake State
  const [step, setStep] = useState<'DETAILS' | 'QUESTIONS' | 'EVALUATED'>('DETAILS');
  const [callId, setCallId] = useState<string>('');
  const [incidentId, setIncidentId] = useState<string>('');
  const [incidentNumber, setIncidentNumber] = useState<string>('');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Triage Results
  const [triageResult, setTriageResult] = useState<{
    priority_tier: string;
    urgency_score: number;
    is_instant_p1_triggered: boolean;
    escalation_reason?: string;
    contributing_factors?: string[];
  } | null>(null);

  if (!isOpen) return null;

  // Preset location quick selectors for easy testing/demo
  const setPreset = (_name: string, pLat: number, pLon: number, pLandmark: string, pType: string) => {
    setLat(pLat);
    setLon(pLon);
    setLandmark(pLandmark);
    setIncidentType(pType);
  };

  const handleStartIntake = async () => {
    setIsSubmitting(true);
    try {
      const res = await api.startCallIntake({
        caller_phone: phone,
        caller_name: callerName,
        latitude: lat,
        longitude: lon,
        address_landmark: landmark,
        initial_incident_type: incidentType
      });

      setCallId(res.call_id);
      setIncidentId(res.provisional_incident_id);
      setIncidentNumber(res.incident_number);
      setQuestions(res.questions);

      // Pre-populate initial answers
      setAnswers({
        Q_EVENT_TYPE: incidentType,
        Q_LOCATION_CONFIRM: landmark,
        Q_CONSCIOUSNESS: 'ALERT',
        Q_BREATHING: 'NORMAL',
        Q_BLEEDING: 'NONE'
      });

      if (res.is_duplicate_detected && res.duplicate_info) {
        onDuplicateDetected(res.duplicate_info, res.call_id);
        onClose();
        return;
      }

      setStep('QUESTIONS');
    } catch (err) {
      alert('Error initializing call intake: ' + err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAnswerChange = (qId: string, val: string) => {
    setAnswers(prev => ({ ...prev, [qId]: val }));
  };

  const handleSubmitAnswers = async () => {
    setIsSubmitting(true);
    try {
      const answerPayload = Object.entries(answers).map(([qId, val]) => ({
        question_id: qId,
        selected_value: val
      }));

      const res = await api.submitAnswers(callId, answerPayload);
      setTriageResult(res);
      setStep('EVALUATED');

      if (res.is_instant_p1_triggered) {
        // Instant P1 triggers immediately!
      }
    } catch (err) {
      alert('Error evaluating triage: ' + err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ padding: '24px' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 700, margin: 0 }}>
              {step === 'DETAILS' && 'New Emergency Call Intake'}
              {step === 'QUESTIONS' && `Essential Triage Vitals — ${incidentNumber}`}
              {step === 'EVALUATED' && 'Triage Assessment & Priority Result'}
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
              Adaptive screening with fail-fast clinical escalation
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '20px',
              cursor: 'pointer'
            }}
          >
            ✕
          </button>
        </div>

        {/* STEP 1: Details */}
        {step === 'DETAILS' && (
          <div>
            {/* Quick Demo Scenario Buttons */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.04)',
              padding: '12px',
              borderRadius: '8px',
              marginBottom: '16px',
              border: '1px solid var(--border-subtle)'
            }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase' }}>
                ⚡ Quick Demo Presets:
              </span>
              <div style={{ display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={() => setPreset('Toll Collision', 11.234123, 78.874123, 'NH-45 Samayapuram Toll Plaza', 'ROAD_TRAFFIC_ACCIDENT')}
                  style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '4px', background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', border: '1px solid rgba(239, 68, 68, 0.4)', cursor: 'pointer' }}
                >
                  Severe Highway Collision (NH-45)
                </button>
                <button
                  type="button"
                  onClick={() => setPreset('Cardiac Chest Pain', 11.234123, 78.874123, 'New Bus Stand, Perambalur', 'CARDIAC_CHEST_PAIN')}
                  style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '4px', background: 'rgba(245, 158, 11, 0.2)', color: '#fde047', border: '1px solid rgba(245, 158, 11, 0.4)', cursor: 'pointer' }}
                >
                  Cardiac Emergency (Bus Stand)
                </button>
                <button
                  type="button"
                  onClick={() => setPreset('Medical College Fall', 11.244123, 78.884123, 'DS Medical College Gate', 'UNCONSCIOUS_FALL')}
                  style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '4px', background: 'rgba(59, 130, 246, 0.2)', color: '#93c5fd', border: '1px solid rgba(59, 130, 246, 0.4)', cursor: 'pointer' }}
                >
                  Severe Trauma / Fall
                </button>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Caller Telephone Number
                </label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-subtle)', color: '#fff', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Caller Name
                </label>
                <input
                  type="text"
                  value={callerName}
                  onChange={(e) => setCallerName(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-subtle)', color: '#fff', fontSize: '13px' }}
                />
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                Incident Type / Category
              </label>
              <select
                value={incidentType}
                onChange={(e) => setIncidentType(e.target.value)}
                style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-subtle)', color: '#fff', fontSize: '13px' }}
              >
                <option value="ROAD_TRAFFIC_ACCIDENT">Vehicle Collision / RTA</option>
                <option value="CARDIAC_CHEST_PAIN">Chest Pain / Cardiac Arrest</option>
                <option value="UNCONSCIOUS_FALL">Unconscious / Severe Fall</option>
                <option value="RESPIRATORY">Severe Respiratory Distress</option>
                <option value="STROKE_NEURO">Stroke / Neurological Collapse</option>
                <option value="OTHER">Other Medical Emergency</option>
              </select>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                Address Landmark / Milestone
              </label>
              <input
                type="text"
                value={landmark}
                onChange={(e) => setLandmark(e.target.value)}
                style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-subtle)', color: '#fff', fontSize: '13px' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
              <button
                type="button"
                onClick={onClose}
                style={{ padding: '9px 16px', borderRadius: '8px', background: 'transparent', border: '1px solid var(--border-subtle)', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleStartIntake}
                disabled={isSubmitting}
                style={{
                  padding: '9px 20px',
                  borderRadius: '8px',
                  background: 'var(--accent-cyan)',
                  border: 'none',
                  color: '#000',
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                {isSubmitting ? 'Starting...' : 'Next: 5 Vital Questions →'}
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: 5 Essential Questions */}
        {step === 'QUESTIONS' && (
          <div>
            <div style={{ maxHeight: '55vh', overflowY: 'auto', paddingRight: '6px' }}>
              {questions.map((q) => (
                <div
                  key={q.question_id}
                  style={{
                    padding: '14px',
                    marginBottom: '12px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    borderRadius: '10px',
                    border: '1px solid var(--border-subtle)'
                  }}
                >
                  <div style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc', marginBottom: '10px' }}>
                    {q.text}
                  </div>

                  {q.question_type === 'SINGLE_CHOICE' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {q.options.map((opt) => {
                        const isSelected = answers[q.question_id] === opt.value;
                        const isInstantP1 = opt.trigger_instant_p1;

                        return (
                          <label
                            key={opt.value}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '10px',
                              padding: '8px 12px',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              background: isSelected
                                ? (isInstantP1 ? 'var(--p1-red-bg)' : 'rgba(6, 182, 212, 0.15)')
                                : 'rgba(0, 0, 0, 0.2)',
                              border: isSelected
                                ? `1px solid ${isInstantP1 ? 'var(--p1-red)' : 'var(--accent-cyan)'}`
                                : '1px solid transparent'
                            }}
                          >
                            <input
                              type="radio"
                              name={q.question_id}
                              value={opt.value}
                              checked={isSelected}
                              onChange={() => handleAnswerChange(q.question_id, opt.value)}
                            />
                            <span style={{ fontSize: '13px', color: isInstantP1 && isSelected ? 'var(--p1-red)' : '#e2e8f0' }}>
                              {opt.label}
                            </span>
                            {isInstantP1 && (
                              <span style={{
                                marginLeft: 'auto',
                                fontSize: '10px',
                                fontWeight: 700,
                                background: 'rgba(239, 68, 68, 0.3)',
                                color: '#fca5a5',
                                padding: '2px 6px',
                                borderRadius: '4px'
                              }}>
                                ⚠️ INSTANT P1 ESCALATION
                              </span>
                            )}
                          </label>
                        );
                      })}
                    </div>
                  )}

                  {q.question_type === 'TEXT' && (
                    <input
                      type="text"
                      value={answers[q.question_id] || ''}
                      onChange={(e) => handleAnswerChange(q.question_id, e.target.value)}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        background: 'var(--bg-input)',
                        border: '1px solid var(--border-subtle)',
                        color: '#fff',
                        fontSize: '13px'
                      }}
                    />
                  )}
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px' }}>
              <button
                type="button"
                onClick={() => setStep('DETAILS')}
                style={{ padding: '8px 14px', borderRadius: '6px', background: 'transparent', border: '1px solid var(--border-subtle)', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                ← Back
              </button>

              <button
                type="button"
                onClick={handleSubmitAnswers}
                disabled={isSubmitting}
                style={{
                  padding: '9px 24px',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #06b6d4, #0284c7)',
                  border: 'none',
                  color: '#fff',
                  fontWeight: 700,
                  cursor: 'pointer',
                  boxShadow: '0 4px 15px rgba(6, 182, 212, 0.3)'
                }}
              >
                {isSubmitting ? 'Evaluating...' : 'Evaluate Triage Urgency ⚡'}
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: Triage Result */}
        {step === 'EVALUATED' && triageResult && (
          <div>
            {/* Instant P1 Banner if Triggered */}
            {triageResult.is_instant_p1_triggered && (
              <div style={{
                padding: '16px',
                borderRadius: '10px',
                background: 'rgba(239, 68, 68, 0.2)',
                border: '2px solid var(--p1-red)',
                marginBottom: '16px',
                animation: 'pulse-red 1.5s infinite'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '24px' }}>🚨</span>
                  <div>
                    <h3 style={{ fontSize: '15px', fontWeight: 800, color: 'var(--p1-red)', margin: 0 }}>
                      INSTANT P1 CRITICAL ESCALATION TRIGGERED
                    </h3>
                    <p style={{ fontSize: '12px', color: '#fca5a5', margin: '4px 0 0 0' }}>
                      {triageResult.escalation_reason || 'Severe threat to life. Bypassing remaining questionnaire.'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Score & Tier Card */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '16px',
              borderRadius: '10px',
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-subtle)',
              marginBottom: '16px'
            }}>
              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Assigned Priority Tier
                </span>
                <div style={{
                  fontSize: '20px',
                  fontWeight: 800,
                  color: triageResult.priority_tier === 'P1_CRITICAL' ? 'var(--p1-red)' : '#f59e0b',
                  marginTop: '4px'
                }}>
                  {triageResult.priority_tier}
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Urgency Score
                </span>
                <div style={{
                  fontSize: '28px',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 800,
                  color: triageResult.urgency_score >= 80 ? 'var(--p1-red)' : '#38bdf8'
                }}>
                  {triageResult.urgency_score} / 100
                </div>
              </div>
            </div>

            {/* Contributing Clinical Factors */}
            <div style={{ marginBottom: '20px' }}>
              <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>
                Clinical Factors & Evidence:
              </span>
              <ul style={{ paddingLeft: '20px', marginTop: '8px', fontSize: '12px', color: '#cbd5e1' }}>
                {(triageResult.contributing_factors || []).map((f, i) => (
                  <li key={i} style={{ marginBottom: '4px' }}>{f}</li>
                ))}
              </ul>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                type="button"
                onClick={() => {
                  onIntakeCompleted(incidentId);
                  onClose();
                }}
                style={{
                  padding: '10px 24px',
                  borderRadius: '8px',
                  background: 'var(--accent-cyan)',
                  border: 'none',
                  color: '#000',
                  fontWeight: 700,
                  fontSize: '13px',
                  cursor: 'pointer'
                }}
              >
                Proceed to AI Dispatch Proposal →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
