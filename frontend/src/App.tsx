import React, { useState, useEffect, useCallback } from 'react';
import { api } from './api/client';
import type { IncidentSummary, Recommendation, AmbulanceFleet, HospitalFacility } from './api/client';
import { Header } from './components/Header';
import { IncidentQueue } from './components/IncidentQueue';
import { RecommendationCard } from './components/RecommendationCard';
import { MapView } from './components/MapView';
import { CallIntakeModal } from './components/CallIntakeModal';
import { DuplicateAlertModal } from './components/DuplicateAlertModal';
import { OverrideModal } from './components/OverrideModal';

export const App: React.FC = () => {
  // Global Operational State
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<IncidentSummary | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [ambulances, setAmbulances] = useState<AmbulanceFleet[]>([]);
  const [hospitals, setHospitals] = useState<HospitalFacility[]>([]);
  const [trafficEnabled, setTrafficEnabled] = useState<boolean>(false);
  const [isLoadingQueue, setIsLoadingQueue] = useState<boolean>(true);
  const [isLoadingRecs, setIsLoadingRecs] = useState<boolean>(false);

  // Modals
  const [isCallModalOpen, setIsCallModalOpen] = useState<boolean>(false);
  const [isDupModalOpen, setIsDupModalOpen] = useState<boolean>(false);
  const [dupInfo, setDupInfo] = useState<any>(null);
  const [dupCallId, setDupCallId] = useState<string>('');
  const [isOverrideModalOpen, setIsOverrideModalOpen] = useState<boolean>(false);
  const [overrideTargetRec, setOverrideTargetRec] = useState<Recommendation | null>(null);

  // Toast Alerts
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Fetch Incidents Queue
  const fetchQueue = useCallback(async () => {
    try {
      const q = await api.getQueue();
      setIncidents(q);
      // If nothing selected or selected incident no longer active, select top item
      if (q.length > 0) {
        setSelectedIncident((prev: IncidentSummary | null) => {
          if (!prev) return q[0];
          const found = q.find(item => item.incident_id === prev.incident_id);
          return found || q[0];
        });
      }
    } finally {
      setIsLoadingQueue(false);
    }
  }, []);

  // Fetch Fleet & Hospitals
  const fetchTelemetry = useCallback(async () => {
    const [ambs, hosps] = await Promise.all([api.getAmbulances(), api.getHospitals()]);
    setAmbulances(ambs);
    setHospitals(hosps);
  }, []);

  // Initial Boot & Telemetry Fetch
  useEffect(() => {
    fetchQueue();
    fetchTelemetry();
    const interval = setInterval(fetchQueue, 4000); // 4-sec polling refresh
    return () => clearInterval(interval);
  }, [fetchQueue, fetchTelemetry]);

  // Fetch Recommendations when Selected Incident changes
  useEffect(() => {
    if (!selectedIncident) {
      setRecommendations([]);
      return;
    }
    const loadRecs = async () => {
      setIsLoadingRecs(true);
      try {
        const recs = await api.getRecommendations(selectedIncident.incident_id);
        setRecommendations(recs);
      } finally {
        setIsLoadingRecs(false);
      }
    };
    loadRecs();
  }, [selectedIncident?.incident_id]);

  // Dispatch Confirmation Handler
  const handleConfirmDispatch = async (rec: Recommendation, isOverride = false, overrideReason: string | null = null) => {
    if (!selectedIncident) return;

    try {
      const res = await api.confirmDispatch({
        incident_id: selectedIncident.incident_id,
        recommendation_id: rec.recommendation_id,
        ambulance_id: rec.ambulance.ambulance_id,
        hospital_id: rec.receiving_hospital.hospital_id,
        operator_id: 'DISPATCHER_42',
        is_override: isOverride,
        override_reason: overrideReason
      });

      showToast(`🚑 Dispatched: ${res.ambulance_code} to Incident ${selectedIncident.incident_number}`);
      fetchQueue();
      fetchTelemetry();
    } catch (err) {
      alert('Error confirming dispatch: ' + err);
    }
  };

  // Active P1 Count
  const p1Count = incidents.filter((i: IncidentSummary) => i.priority_tier === 'P1_CRITICAL').length;
  const activeRec = recommendations[0] || null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* Toast Notification Banner */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          top: '70px',
          right: '24px',
          zIndex: 9999,
          background: 'linear-gradient(135deg, #10b981, #059669)',
          color: '#fff',
          padding: '12px 20px',
          borderRadius: '8px',
          fontWeight: 700,
          fontSize: '13px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
          animation: 'fadeIn 0.3s ease'
        }}>
          {toastMessage}
        </div>
      )}

      {/* Top Cockpit Header */}
      <Header
        onNewCall={() => setIsCallModalOpen(true)}
        trafficEnabled={trafficEnabled}
        onToggleTraffic={() => {
          setTrafficEnabled((prev: boolean) => !prev);
          showToast(`Traffic congestion factor updated: ${!trafficEnabled ? 'PEAK 1.4x' : 'NORMAL'}`);
        }}
        activeCount={incidents.length}
        p1Count={p1Count}
      />

      {/* Main 3-Pane Cockpit Layout */}
      <main style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: '340px 1.1fr 1fr',
        gap: '12px',
        padding: '12px',
        minHeight: 0
      }}>
        {/* Pane 1 (Left): Live Priority Queue */}
        <section style={{ minHeight: 0 }}>
          <IncidentQueue
            incidents={incidents}
            selectedId={selectedIncident?.incident_id || null}
            onSelect={(inc) => setSelectedIncident(inc)}
            isLoading={isLoadingQueue}
          />
        </section>

        {/* Pane 2 (Center): AI Recommendation Dossier */}
        <section style={{ minHeight: 0 }}>
          <RecommendationCard
            incident={selectedIncident}
            recommendations={recommendations}
            onConfirmDispatch={(rec) => handleConfirmDispatch(rec, false)}
            onOpenOverride={(rec) => {
              setOverrideTargetRec(rec);
              setIsOverrideModalOpen(true);
            }}
            isLoading={isLoadingRecs}
          />
        </section>

        {/* Pane 3 (Right): Interactive OpenStreetMap & Dijkstra Route Map */}
        <section style={{ minHeight: 0 }}>
          <MapView
            ambulances={ambulances}
            hospitals={hospitals}
            selectedIncident={selectedIncident}
            activeRecommendation={activeRec}
          />
        </section>
      </main>

      {/* Call Intake Wizard Modal */}
      <CallIntakeModal
        isOpen={isCallModalOpen}
        onClose={() => setIsCallModalOpen(false)}
        onIntakeCompleted={(incId) => {
          fetchQueue();
          showToast(`Emergency Intake logged. Incident ${incId.slice(0, 8)}... created.`);
        }}
        onDuplicateDetected={(info, callId) => {
          setDupInfo(info);
          setDupCallId(callId);
          setIsDupModalOpen(true);
        }}
      />

      {/* Duplicate Alert Modal */}
      <DuplicateAlertModal
        isOpen={isDupModalOpen}
        dupInfo={dupInfo}
        newCallId={dupCallId}
        onClose={() => setIsDupModalOpen(false)}
        onMerged={(incId) => {
          fetchQueue();
          showToast(`Call consolidated into Incident ${incId.slice(0, 8)}...`);
        }}
      />

      {/* Manual Override Modal */}
      <OverrideModal
        isOpen={isOverrideModalOpen}
        recommendation={overrideTargetRec}
        onClose={() => setIsOverrideModalOpen(false)}
        onSubmitOverride={(reason) => {
          if (overrideTargetRec) {
            handleConfirmDispatch(overrideTargetRec, true, reason);
            setIsOverrideModalOpen(false);
          }
        }}
      />
    </div>
  );
};

export default App;
