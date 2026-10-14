-- PriorityCare PostgreSQL Relational Schema & Spatial Setup
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table 1: Hospitals
CREATE TABLE IF NOT EXISTS hospitals (
    hospital_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    specialties TEXT[] NOT NULL DEFAULT '{}',
    icu_beds_available INTEGER NOT NULL DEFAULT 0,
    general_beds_available INTEGER NOT NULL DEFAULT 0,
    is_accepting_emergencies BOOLEAN NOT NULL DEFAULT TRUE,
    contact_phone VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Table 2: Ambulances
CREATE TABLE IF NOT EXISTS ambulances (
    ambulance_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vehicle_code VARCHAR(50) UNIQUE NOT NULL,
    ambulance_type VARCHAR(20) NOT NULL, -- ALS, BLS, PTS
    status VARCHAR(30) NOT NULL DEFAULT 'AVAILABLE',
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    base_station_name VARCHAR(255) NOT NULL,
    staff_qualifications TEXT[] NOT NULL DEFAULT '{}',
    onboard_equipment TEXT[] NOT NULL DEFAULT '{}',
    current_incident_id UUID,
    last_location_update TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Table 3: Incidents
CREATE TABLE IF NOT EXISTS incidents (
    incident_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_number VARCHAR(50) UNIQUE NOT NULL,
    incident_type VARCHAR(100) NOT NULL,
    description TEXT,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    address_landmark VARCHAR(255) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'REPORTED',
    priority_tier VARCHAR(20) NOT NULL DEFAULT 'P2_HIGH_URGENCY',
    urgency_score INTEGER NOT NULL DEFAULT 50,
    affected_casualty_count INTEGER NOT NULL DEFAULT 1,
    is_trapped BOOLEAN NOT NULL DEFAULT FALSE,
    scene_hazards TEXT[] NOT NULL DEFAULT '{}',
    active_ambulance_id UUID REFERENCES ambulances(ambulance_id),
    target_hospital_id UUID REFERENCES hospitals(hospital_id),
    call_count INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Table 4: Call Reports
CREATE TABLE IF NOT EXISTS call_reports (
    call_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(incident_id) ON DELETE CASCADE,
    caller_phone_hash VARCHAR(128) NOT NULL,
    caller_name VARCHAR(100),
    reported_latitude DOUBLE PRECISION NOT NULL,
    reported_longitude DOUBLE PRECISION NOT NULL,
    reported_landmark VARCHAR(255),
    reported_casualties INTEGER NOT NULL DEFAULT 1,
    caller_statement TEXT,
    dedup_confidence NUMERIC(4, 2),
    call_start_time TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    call_end_time TIMESTAMP WITH TIME ZONE
);

-- Table 5: Assessment Answers
CREATE TABLE IF NOT EXISTS assessment_answers (
    answer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(incident_id) ON DELETE CASCADE,
    call_id UUID NOT NULL REFERENCES call_reports(call_id) ON DELETE CASCADE,
    question_id VARCHAR(100) NOT NULL,
    selected_value VARCHAR(100) NOT NULL,
    raw_answer_text TEXT,
    answered_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Table 6: Priority Assessments Audit
CREATE TABLE IF NOT EXISTS priority_assessments (
    assessment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(incident_id) ON DELETE CASCADE,
    calculated_score INTEGER NOT NULL,
    assigned_tier VARCHAR(20) NOT NULL,
    rule_version VARCHAR(50) NOT NULL,
    contributing_factors TEXT[] NOT NULL DEFAULT '{}',
    is_instant_escalation BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Table 7: Dispatch Recommendations
CREATE TABLE IF NOT EXISTS dispatch_recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(incident_id) ON DELETE CASCADE,
    ambulance_id UUID NOT NULL REFERENCES ambulances(ambulance_id),
    hospital_id UUID NOT NULL REFERENCES hospitals(hospital_id),
    eta_to_scene_seconds INTEGER NOT NULL,
    distance_to_scene_meters INTEGER NOT NULL,
    eta_to_hospital_seconds INTEGER NOT NULL,
    distance_to_hospital_meters INTEGER NOT NULL,
    suitability_match_score NUMERIC(4, 2) NOT NULL,
    suitability_reason TEXT NOT NULL,
    scene_route_geometry JSONB NOT NULL,
    hospital_route_geometry JSONB NOT NULL,
    is_selected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Table 8: Dispatch Actions (Operator Audit Trail)
CREATE TABLE IF NOT EXISTS dispatch_actions (
    action_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(incident_id),
    recommendation_id UUID REFERENCES dispatch_recommendations(recommendation_id),
    ambulance_id UUID NOT NULL REFERENCES ambulances(ambulance_id),
    hospital_id UUID NOT NULL REFERENCES hospitals(hospital_id),
    operator_id VARCHAR(100) NOT NULL,
    is_override BOOLEAN NOT NULL DEFAULT FALSE,
    override_reason TEXT,
    action_timestamp TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Indexes for Fast Query Execution
CREATE INDEX IF NOT EXISTS idx_incidents_queue ON incidents(status, priority_tier, urgency_score DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_incidents_location ON incidents(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_ambulances_status ON ambulances(status, ambulance_type);
CREATE INDEX IF NOT EXISTS idx_calls_incident ON call_reports(incident_id);
