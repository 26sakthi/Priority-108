const API_BASE = "http://localhost:8000/api/v1";

export interface IncidentSummary {
  incident_id: string;
  incident_number: string;
  incident_type: string;
  description: string | null;
  priority_tier: "P1_CRITICAL" | "P2_HIGH_URGENCY" | "P3_LOWER_URGENCY";
  urgency_score: number;
  affected_casualty_count: number;
  status: string;
  address_landmark: string;
  latitude: number;
  longitude: number;
  is_trapped: boolean;
  scene_hazards: string[];
  call_count: number;
  created_at: string;
  assigned_ambulance?: {
    ambulance_id: string;
    vehicle_code: string;
    ambulance_type: string;
    status: string;
  } | null;
  target_hospital?: {
    hospital_id: string;
    name: string;
  } | null;
}

export interface QuestionOption {
  value: string;
  label: string;
  urgency_weight: number;
  trigger_instant_p1: boolean;
}

export interface Question {
  question_id: string;
  text: string;
  question_type: string;
  options: QuestionOption[];
  is_essential: boolean;
  category?: string;
}

export interface Recommendation {
  recommendation_id: string;
  rank: number;
  ambulance: {
    ambulance_id: string;
    vehicle_code: string;
    ambulance_type: string;
    status: string;
    latitude: number;
    longitude: number;
    base_station: string;
    staff: string[];
    equipment: string[];
  };
  eta_to_scene_seconds: number;
  distance_to_scene_meters: number;
  receiving_hospital: {
    hospital_id: string;
    name: string;
    latitude: number;
    longitude: number;
    specialties: string[];
    icu_beds_available: number;
    general_beds_available: number;
    is_accepting_emergencies: boolean;
    contact_phone?: string;
    eta_to_hospital_seconds?: number;
    distance_to_hospital_meters?: number;
    specialty_matched?: string;
  };
  suitability_score: number;
  recommendation_rationale: string;
  scene_route: {
    type: string;
    coordinates: number[][]; // [lon, lat]
  };
  hospital_route: {
    type: string;
    coordinates: number[][];
  };
}

export interface AmbulanceFleet {
  ambulance_id: string;
  vehicle_code: string;
  ambulance_type: string;
  status: string;
  latitude: number;
  longitude: number;
  base_station: string;
  staff: string[];
  equipment: string[];
  current_incident_id?: string;
}

export interface HospitalFacility {
  hospital_id: string;
  name: string;
  latitude: number;
  longitude: number;
  specialties: string[];
  icu_beds_available: number;
  general_beds_available: number;
  is_accepting_emergencies: boolean;
  contact_phone?: string;
}

export const api = {
  async getQueue(): Promise<IncidentSummary[]> {
    try {
      const res = await fetch(`${API_BASE}/incidents?status=ACTIVE`);
      const json = await res.json();
      return json.data.queue;
    } catch {
      return [];
    }
  },

  async startCallIntake(payload: {
    caller_phone: string;
    caller_name?: string;
    latitude: number;
    longitude: number;
    address_landmark: string;
    initial_incident_type: string;
  }) {
    const res = await fetch(`${API_BASE}/calls/intake`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return (await res.json()).data;
  },

  async submitAnswers(callId: string, answers: { question_id: string; selected_value: string }[]) {
    const res = await fetch(`${API_BASE}/calls/${callId}/answers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answers })
    });
    return (await res.json()).data;
  },

  async checkDuplicate(payload: {
    latitude: number;
    longitude: number;
    incident_type: string;
    landmark?: string;
    reported_casualties: number;
  }) {
    const res = await fetch(`${API_BASE}/incidents/check-duplicate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return (await res.json()).data;
  },

  async mergeCall(incidentId: string, payload: {
    call_id: string;
    updated_casualty_count: number;
    additional_notes?: string;
  }) {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/merge-call`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return (await res.json()).data;
  },

  async getRecommendations(incidentId: string): Promise<Recommendation[]> {
    try {
      const res = await fetch(`${API_BASE}/incidents/${incidentId}/recommendations`);
      const json = await res.json();
      return json.data.recommendations;
    } catch {
      return [];
    }
  },

  async confirmDispatch(payload: {
    incident_id: string;
    recommendation_id?: string;
    ambulance_id: string;
    hospital_id: string;
    operator_id: string;
    is_override?: boolean;
    override_reason?: string | null;
  }) {
    const res = await fetch(`${API_BASE}/dispatch/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return (await res.json()).data;
  },

  async getAmbulances(): Promise<AmbulanceFleet[]> {
    try {
      const res = await fetch(`${API_BASE}/ambulances`);
      const json = await res.json();
      return json.data;
    } catch {
      return [];
    }
  },

  async getHospitals(): Promise<HospitalFacility[]> {
    try {
      const res = await fetch(`${API_BASE}/hospitals`);
      const json = await res.json();
      return json.data;
    } catch {
      return [];
    }
  }
};
