# PriorityCare (MEDI-DISPATCH AI) — Product Requirements Document (PRD) & Shared Data Contract

**Document Version:** 1.1.0-RELEASE (Automatic Assignment Update)  
**Document Status:** Approved Data & API Contract Baseline  
**Project Repository:** PriorityCare (INTELLATHON '26 — Team JARVIS)  
**System Type:** Modular Monolith Emergency Dispatch Decision-Support System  
**Target Environment:** 112 / 108 Emergency Operations Control Center (Automated Dispatch Copilot)  

---

## 1. Document Overview & Team Ownership

This document establishes the single source of truth for PriorityCare's product requirements, domain entities, database schema, and REST API contract. All four team members must develop their modules against these interfaces to ensure zero-friction integration.

### 1.1 Team Roles & Modular Ownership Matrix

| Teammate | Focus Area | Specific Modular Ownership | Deliverable Responsibility |
| :--- | :--- | :--- | :--- |
| **Teammate A (Lead / User)** | **AI, Auto-Assignment & Architecture** | • Automatic ambulance assignment engine (EST, location, availability, queue rank).<br/>• Hospital capability & Dijkstra routing engine.<br/>• System Architecture & PRD.<br/>• PostgreSQL schema & PostGIS queries. | • `app/services/auto_assignment_engine.py`<br/>• `app/services/routing_engine.py`<br/>• `app/models/` (SQLAlchemy)<br/>• `db/init.sql` (PostgreSQL DDL) |
| **Teammate B** | **Research & Decision Logic** | • Dynamic clinical questioning decision trees.<br/>• P1/P2/P3 priority scoring formulas.<br/>• Clinical tie-breaking and escalation rules. | • `docs/TRIAGE_SPEC.md`<br/>• `docs/QUESTION_BANK.json`<br/>• Priority scoring weights & rubrics |
| **Teammate C** | **Backend Core & Integration** | • Dynamic question engine implementation.<br/>• Priority calculation service implementation.<br/>• Spatial-temporal duplicate detection.<br/>• FastAPI routes & master branch integration. | • `app/services/question_engine.py`<br/>• `app/services/priority_engine.py`<br/>• `app/services/dedup_engine.py`<br/>• `app/api/v1/` routes & tests |
| **Teammate D** | **UI/UX & Frontend** | • React Dispatcher Dashboard.<br/>• Live Priority Queue view.<br/>• Dynamic Question intake form.<br/>• Live Auto-Assignment & OpenStreetMap (OSM) map view. | • `frontend/src/components/`<br/>• `frontend/src/api/client.ts`<br/>• Figma prototype & UI integration |

---

## 2. System Overview & Problem Statement

### 2.1 The Operational Bottleneck
Emergency call centres (such as 112/108) experience severe cognitive overload during multi-casualty incidents or call surges. Traditional workflows suffer from:
1. **Sequential Questioning Delays:** Rigid intake scripts delay dispatching units to unconscious or dying patients.
2. **Duplicate Call Chaos:** Multiple bystanders report the same crash, causing confusion or redundant vehicle dispatches while other emergencies wait unserved.
3. **Casualty Count Dilution:** Naive deduplication wipes out critical updates (e.g., a 3rd caller reporting 2 trapped victims).
4. **Manual Proximity Dispatch Bottleneck:** Forcing operators to manually browse map icons and pick an ambulance causes decision paralysis and delays during call surges.
5. **Secondary Hospital Transfer Crisis:** Ambulances deliver patients to the nearest hospital only to find it lacks an open trauma ICU or cath lab.

### 2.2 The PriorityCare Solution
PriorityCare provides an automated **dispatch copilot** for the control room:
* **Adaptive Triage Intake:** A 5-question baseline with instant **P1 Fail-Fast Escalation** (if breathing/consciousness is absent, alert fires in $<10$ seconds).
* **Multi-Factor Duplicate Linking:** Links calls based on radius + time window + incident type, preserving cumulative casualty counts.
* **Automatic Ambulance Assignment Engine:** Automatically evaluates the prioritized incident queue ($P1 > P2 > P3$, then urgency score descending) and instantly assigns the optimal available ambulance based on:
  1. **Operational Availability:** Unit must be `AVAILABLE`.
  2. **Clinical Suitability:** Matches patient severity to vehicle capabilities (`ALS` with ventilator/defibrillator for P1; `BLS` for P2).
  3. **EST / ETA (Estimated Travel Time):** Dijkstra shortest-path travel time over the road network to the incident scene.
* **Suitability-First Hospital Routing:** Uses Dijkstra’s shortest-path algorithm over an OpenStreetMap road graph to deliver patients directly to an appropriately equipped and available hospital.
* **Supervisory Operator Authority:** The system automatically executes assignment and alerts the unit, while the operator retains supervisory control to review, monitor, or execute a **Manual Override / Reassignment** with an audit reason code.

---

## 3. Global Technical Standards & Conventions

All modules, APIs, and data structures must strictly adhere to these conventions:

| Parameter | Standard Convention | Example / Rule |
| :--- | :--- | :--- |
| **Identifier Format** | UUID v4 (strings) | `"e2b83490-671b-4f7d-8157-1901b0f51234"` |
| **Naming Convention** | `snake_case` | Backend models, JSON request/response payloads, and React state attributes must all use `snake_case`. |
| **Timestamps** | ISO 8601 UTC | `"2026-10-14T12:30:00Z"` |
| **Coordinates** | Decimal Degrees (WGS 84) | `latitude`: `11.234123`, `longitude`: `78.874123` |
| **Distance Unit** | Meters (integer / float) | `4500` (represents 4.5 km) |
| **Duration Unit** | Seconds (integer / float) | `720` (represents 12 minutes) |
| **Speed Unit** | Kilometers per hour (km/h) | `45.0` |
| **Coordinate Object** | Reusable Geo-JSON style pair | `{"latitude": 11.234, "longitude": 78.874}` |
| **Architecture** | FastAPI Modular Monolith | Synchronous REST + JSON payloads |

---

## 4. Core Domain Entities & Shared Schema

### 4.1 Enumerated Types (Enums)

```python
# Incident Status Lifecycle
class IncidentStatus(str, Enum):
    REPORTED = "REPORTED"            # Initial call in intake
    TRIAGED = "TRIAGED"              # Questioning complete, priority assigned
    PENDING_ASSIGNMENT = "PENDING_ASSIGNMENT" # In queue awaiting available ambulance
    AUTO_ASSIGNED = "AUTO_ASSIGNED"  # Ambulance automatically assigned by engine
    DISPATCHED = "DISPATCHED"        # Unit dispatched and en route to scene
    ON_SCENE = "ON_SCENE"            # Ambulance arrived at incident location
    TRANSPORTING = "TRANSPORTING"    # En route to receiving hospital
    RESOLVED = "RESOLVED"            # Patient handed over / incident closed
    CANCELLED = "CANCELLED"          # False alarm or duplicate cancelled

# Clinical Priority Tiers
class PriorityTier(str, Enum):
    P1_CRITICAL = "P1_CRITICAL"          # Immediate threat to life (unconscious, not breathing, massive trauma)
    P2_HIGH_URGENCY = "P2_HIGH_URGENCY"  # Severe illness/injury requiring urgent stabilization
    P3_LOWER_URGENCY = "P3_LOWER_URGENCY"# Stable / minor injury / non-emergency

# Ambulance Capability Levels
class AmbulanceType(str, Enum):
    ALS = "ALS"  # Advanced Life Support (Paramedic, Ventilator, Defibrillator)
    BLS = "BLS"  # Basic Life Support (EMT, Oxygen, First Aid, AED)
    PTS = "PTS"  # Patient Transport Service (Basic mobility, non-critical)

# Operational Ambulance Status
class AmbulanceStatus(str, Enum):
    AVAILABLE = "AVAILABLE"              # In base or roaming, ready for dispatch
    ASSIGNED = "ASSIGNED"                # Automatically assigned to an incident
    EN_ROUTE_SCENE = "EN_ROUTE_SCENE"    # Moving toward incident
    AT_SCENE = "AT_SCENE"                # Paramedics treating at location
    EN_ROUTE_HOSPITAL = "EN_ROUTE_HOSPITAL" # Moving to receiving facility
    AT_HOSPITAL = "AT_HOSPITAL"          # Transferring patient to ER
    MAINTENANCE = "MAINTENANCE"          # Refueling, sanitizing, or offline

# Duplicate Match Confidence Level
class MatchConfidence(str, Enum):
    HIGH_MATCH = "HIGH_MATCH"            # Automatic link recommended (>85% match)
    UNCERTAIN_MATCH = "UNCERTAIN_MATCH"  # Flagged for operator review (50%-85%)
    NO_MATCH = "NO_MATCH"                # Distinct new incident (<50%)

# Hospital Medical Specialty Capabilities
class FacilitySpecialty(str, Enum):
    TRAUMA_LEVEL_1 = "TRAUMA_LEVEL_1"
    CARDIAC_CATH_LAB = "CARDIAC_CATH_LAB"
    BURN_CARE = "BURN_CARE"
    NEUROLOGY = "NEUROLOGY"
    PEDIATRIC_ICU = "PEDIATRIC_ICU"
    GENERAL_EMERGENCY = "GENERAL_EMERGENCY"
```

---

### 4.2 Entity 1: Incident (The Core Operational Record)
An `Incident` represents a verified or active emergency event. Multiple emergency calls can be linked to a single incident.

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `incident_id` | UUID (string) | Yes | Primary Key. Unique identifier. |
| `incident_number` | String | Yes | Human-readable identifier (e.g., `"INC-20261014-0012"`). |
| `incident_type` | String | Yes | Category: `"ROAD_TRAFFIC_ACCIDENT"`, `"CARDIAC_CHEST_PAIN"`, `"STROKE"`, `"TRAUMA"`, `"RESPIRATORY"`, `"OTHER"`. |
| `description` | String | No | Free-text operational summary of the incident. |
| `latitude` | Float | Yes | Geographic latitude (-90 to +90). |
| `longitude` | Float | Yes | Geographic longitude (-180 to +180). |
| `address_landmark` | String | Yes | Human-readable street address or landmark (e.g., `"NH-45 Toll Gate"`). |
| `status` | `IncidentStatus` | Yes | Current lifecycle state. Default: `REPORTED`. |
| `priority_tier` | `PriorityTier` | Yes | Current priority tier. Default: `P2_HIGH_URGENCY`. |
| `urgency_score` | Integer | Yes | Calculated urgency score `(0 - 100)`. Higher = more urgent. |
| `affected_casualty_count` | Integer | Yes | Cumulative count of injured casualties. Default: `1`. |
| `is_trapped` | Boolean | Yes | Indicates if casualties are mechanically trapped. Default: `False`. |
| `scene_hazards` | List[String] | Yes | Detected hazards (e.g., `["FUEL_LEAK", "FIRE", "LIVE_WIRE"]`). |
| `active_ambulance_id` | UUID (string) | No | Reference to automatically assigned ambulance. |
| `target_hospital_id` | UUID (string) | No | Reference to automatically selected destination hospital. |
| `call_count` | Integer | Yes | Number of distinct incoming calls linked to this incident. |
| `created_at` | ISO 8601 UTC | Yes | Timestamp when the first call was received. |
| `updated_at` | ISO 8601 UTC | Yes | Timestamp of most recent update or call link. |

---

### 4.3 Entity 2: CallReport (Individual Call Record & Deduplication Child)
Every phone call received creates a `CallReport`. One incident contains one or more `CallReport`s.

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `call_id` | UUID (string) | Yes | Primary Key. |
| `incident_id` | UUID (string) | Yes | Foreign Key referencing parent `Incident`. |
| `caller_phone_hash` | String | Yes | Pseudonymized / masked caller telephone number for privacy. |
| `caller_name` | String | No | Caller name if provided. |
| `reported_latitude` | Float | Yes | Location given during this specific call. |
| `reported_longitude` | Float | Yes | Location given during this specific call. |
| `reported_landmark` | String | Yes | Specific landmark mentioned by this caller. |
| `reported_casualties` | Integer | Yes | Casualty count reported by this specific caller. |
| `caller_statement` | String | No | Short notes recorded by the operator. |
| `dedup_confidence` | Float | No | Similarity match score `(0.00 - 1.00)` against parent incident. |
| `call_start_time` | ISO 8601 UTC | Yes | Timestamp call connected. |
| `call_end_time` | ISO 8601 UTC | No | Timestamp call completed. |

---

### 4.4 Entity 3: Dynamic Question & Answer Log

#### Question Definition Model (Question Bank)
```json
{
  "question_id": "Q_BREATHING_01",
  "category": "ESSENTIAL",
  "text": "Is the patient conscious and breathing normally?",
  "question_type": "SINGLE_CHOICE",
  "options": [
    {"value": "NORMAL", "label": "Conscious & breathing normally", "urgency_weight": 0},
    {"value": "DIFFICULT", "label": "Conscious but severe breathing difficulty", "urgency_weight": 35},
    {"value": "UNRESPONSIVE_BREATHING", "label": "Unconscious but breathing", "urgency_weight": 70},
    {"value": "NO_BREATHING", "label": "Unconscious and NOT breathing / gasping", "urgency_weight": 100, "trigger_instant_p1": true}
  ],
  "is_essential": true,
  "trigger_condition": null
}
```

#### Assessment Answer Record (Stored in Database)
| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `answer_id` | UUID (string) | Yes | Primary Key. |
| `incident_id` | UUID (string) | Yes | Associated incident. |
| `call_id` | UUID (string) | Yes | Associated call intake. |
| `question_id` | String | Yes | Question identifier (e.g., `"Q_BREATHING_01"`). |
| `selected_value` | String | Yes | Normalized answer code (e.g., `"NO_BREATHING"`). |
| `raw_answer_text` | String | No | Free-form detail if question type is text/numeric. |
| `answered_at` | ISO 8601 UTC | Yes | Timestamp when the answer was recorded. |

---

### 4.5 Entity 4: Priority Assessment (Audit Snapshot)
Every time answers change or a call links to an incident, a `PriorityAssessment` audit record is created.

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `assessment_id` | UUID (string) | Yes | Primary Key. |
| `incident_id` | UUID (string) | Yes | Foreign Key referencing `Incident`. |
| `calculated_score` | Integer | Yes | Composite urgency score `(0 - 100)`. |
| `assigned_tier` | `PriorityTier` | Yes | Resulting priority tier (`P1_CRITICAL`, `P2_HIGH_URGENCY`, `P3_LOWER_URGENCY`). |
| `rule_version` | String | Yes | Triage rule algorithm version (e.g., `"TRIAGE-RULE-v1.0"`). |
| `contributing_factors`| List[String] | Yes | Explanation reasons (e.g., `["Absent respiration (+100)", "Immediate P1 rule triggered"]`). |
| `is_instant_escalation`| Boolean | Yes | True if triggered by critical vitals before question completion. |
| `created_at` | ISO 8601 UTC | Yes | Timestamp of calculation. |

---

### 4.6 Entity 5: Ambulance (Vehicle Unit)

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `ambulance_id` | UUID (string) | Yes | Primary Key. |
| `vehicle_code` | String | Yes | Unit identifier (e.g., `"AMB-TN-04"`). |
| `ambulance_type` | `AmbulanceType` | Yes | `ALS`, `BLS`, or `PTS`. |
| `status` | `AmbulanceStatus` | Yes | Current operational availability. |
| `latitude` | Float | Yes | Current GPS latitude. |
| `longitude` | Float | Yes | Current GPS longitude. |
| `base_station_name` | String | Yes | Name of assigned base/station (e.g., `"Perambalur GH Depot"`). |
| `staff_qualifications`| List[String] | Yes | Crew skills (e.g., `["PARAMEDIC_ADVANCED", "VENTILATOR_CERTIFIED"]`). |
| `onboard_equipment` | List[String] | Yes | Available equipment: `["DEFIBRILLATOR", "VENTILATOR", "OXYGEN", "TRAUMA_KIT"]`. |
| `current_incident_id` | UUID (string) | No | Currently assigned incident, if not available. |
| `last_location_update`| ISO 8601 UTC | Yes | Timestamp of latest GPS ping. |

---

### 4.7 Entity 6: Hospital / Medical Receiving Facility

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `hospital_id` | UUID (string) | Yes | Primary Key. |
| `name` | String | Yes | Hospital name (e.g., `"Dhanalakshmi Srinivasan Medical College Hospital"`). |
| `latitude` | Float | Yes | Gate / Emergency entrance latitude. |
| `longitude` | Float | Yes | Gate / Emergency entrance longitude. |
| `specialties` | List[`FacilitySpecialty`] | Yes | Clinical capabilities (e.g., `["TRAUMA_LEVEL_1", "CARDIAC_CATH_LAB", "NEUROLOGY"]`). |
| `icu_beds_available` | Integer | Yes | Current open ICU beds. |
| `general_beds_available`| Integer | Yes | Current open emergency ward beds. |
| `is_accepting_emergencies`| Boolean | Yes | Emergency department status. Default: `True`. |
| `contact_phone` | String | Yes | Direct trauma room phone number. |

---

### 4.8 Entity 7: DispatchAssignment (Automated Unit Assignment)
Generated automatically by the Automatic Ambulance Assignment Engine (Teammate A).

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `assignment_id` | UUID (string) | Yes | Primary Key. |
| `incident_id` | UUID (string) | Yes | Incident assigned to. |
| `ambulance_id` | UUID (string) | Yes | Automatically assigned vehicle. |
| `hospital_id` | UUID (string) | Yes | Automatically assigned receiving hospital. |
| `queue_priority_rank` | Integer | Yes | Position in the priority queue at the moment of assignment. |
| `est_travel_seconds` | Integer | Yes | Estimated Travel Time (EST / ETA) to incident in seconds. |
| `distance_to_scene_meters`| Integer | Yes | Network route distance to incident in meters. |
| `est_to_hospital_seconds`| Integer | Yes | Estimated travel time from incident to hospital in seconds. |
| `distance_to_hospital_meters`| Integer | Yes | Distance from incident to hospital in meters. |
| `suitability_score` | Float | Yes | Capability match score `(0.00 - 1.00)`. |
| `assignment_rationale` | String | Yes | Explanation (e.g., `"Auto-Assigned: Nearest available ALS unit (EST: 8m) for top-priority P1 Cardiac emergency"`). |
| `scene_route_geometry` | GeoJSON LineString | Yes | Coordinates sequence for ambulance-to-incident path. |
| `hospital_route_geometry`| GeoJSON LineString | Yes | Coordinates sequence for incident-to-hospital path. |
| `is_overridden` | Boolean | Yes | True if the operator subsequently overrode this auto-assignment. |
| `assigned_at` | ISO 8601 UTC | Yes | Exact auto-assignment timestamp. |

---

### 4.9 Entity 8: DispatchAction (Audit Log)

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `action_id` | UUID (string) | Yes | Primary Key. |
| `incident_id` | UUID (string) | Yes | Target incident. |
| `assignment_id` | UUID (string) | No | Associated automated assignment record. |
| `ambulance_id` | UUID (string) | Yes | Active ambulance. |
| `hospital_id` | UUID (string) | Yes | Destination hospital. |
| `operator_id` | String | Yes | Operator username or badge number. |
| `action_type` | String | Yes | `"AUTO_ASSIGN_ACK"`, `"MANUAL_OVERRIDE"`, `"REASSIGNMENT"`, `"CANCEL"`. |
| `override_reason` | String | No | Mandatory explanation if operator overrides the automated assignment. |
| `action_timestamp` | ISO 8601 UTC | Yes | Exact time confirmation or override was executed. |

---

## 5. Detailed REST API Contract

Base URL: `/api/v1`  
All response payloads follow the standard Response Envelope:
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

---

### 5.1 Call Intake & Dynamic Questioning API (Owned by Teammate C & B)

#### 1. Start Call Intake & Get Essential Questions
* **`POST /api/v1/calls/intake`**
* **Request Body:** Caller phone, landmark, coordinates, and initial event type.
* **Response (201 Created):** Returns `call_id`, provisional `incident_id`, duplicate detection status, and the 5 essential screening questions.

#### 2. Submit Answers & Evaluate Triage
* **`POST /api/v1/calls/{call_id}/answers`**
* **Description:** Submits answers. If P1 conditions are met (e.g., absent breathing), triggers instant P1 escalation and immediately triggers the **Automatic Ambulance Assignment Engine**.

---

### 5.2 Duplicate Detection API (Owned by Teammate C & A)

#### 1. Check for Duplicate Incident
* **`POST /api/v1/incidents/check-duplicate`**
* **Description:** Analyzes whether an incoming call matches an active incident within spatial radius (500m) and temporal window (20 min).

#### 2. Confirm Call Merge to Existing Incident
* **`POST /api/v1/incidents/{incident_id}/merge-call`**
* **Description:** Merges a call into an existing incident, updating casualty count cumulatively ($\max(\text{reported}, \text{current})$) without creating duplicate incidents.

---

### 5.3 Priority Queue & Incident Management API (Owned by Teammate C & D)

#### 1. Get Prioritized Incident Queue
* **`GET /api/v1/incidents?status=ACTIVE`**
* **Description:** Returns the live sorted queue of active incidents.
* **Ordering Logic:** `priority_tier` ($P1 > P2 > P3$), then `urgency_score` (descending), then `created_at` (ascending). Shows automatically assigned ambulance and EST.

---

### 5.4 Automatic Ambulance Assignment & Routing API (Owned by Teammate A)

#### 1. Trigger Automatic Queue Assignment
* **`POST /api/v1/dispatch/auto-assign`**
* **Description:** Evaluates active incidents in the priority queue and automatically assigns the best available ambulances based on EST, location, availability, and capability suitability.
* **Request Body:**
```json
{
  "incident_id": "i9f8e7d6-1111-4000-b000-999988887777"
}
```
* **Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "assignment_id": "r1a1b1c1-9999-4000-d000-111111111111",
    "incident_id": "i9f8e7d6-1111-4000-b000-999988887777",
    "incident_status": "AUTO_ASSIGNED",
    "ambulance": {
      "ambulance_id": "a1b2c3d4-1111-4000-e000-111122223333",
      "vehicle_code": "AMB-ALS-02",
      "ambulance_type": "ALS",
      "status": "ASSIGNED",
      "base_station": "Trichy Medical College Depot"
    },
    "est_travel_seconds": 480,
    "distance_to_scene_meters": 4200,
    "receiving_hospital": {
      "hospital_id": "h1b2c3d4-2222-4000-f000-444455556666",
      "name": "Dhanalakshmi Srinivasan Medical College Hospital",
      "specialty_matched": "TRAUMA_LEVEL_1",
      "est_to_hospital_seconds": 720
    },
    "assignment_rationale": "Auto-Assigned: Nearest available ALS unit (EST: 8m) matched for top-priority P1 Severe Trauma. Hospital B selected for active Level-1 Trauma ICU.",
    "scene_route": {
      "type": "LineString",
      "coordinates": [[78.854123, 11.214123], [78.874123, 11.234123]]
    },
    "hospital_route": {
      "type": "LineString",
      "coordinates": [[78.874123, 11.234123], [78.894123, 11.254123]]
    }
  },
  "message": "Ambulance automatically assigned successfully"
}
```

---

#### 2. Get Incident Assignment Dossier
* **`GET /api/v1/incidents/{incident_id}/assignment`**
* **Description:** Retrieves the active automated assignment, assigned ambulance status, live EST, and hospital route.

---

#### 3. Operator Manual Override & Reassignment (Supervisory Control)
* **`POST /api/v1/dispatch/override`**
* **Description:** Operator overrides the automatic assignment (e.g. reassigns to another vehicle, cancels, or alters destination hospital) with a mandatory audit reason code.
* **Request Body:**
```json
{
  "incident_id": "i9f8e7d6-1111-4000-b000-999988887777",
  "assignment_id": "r1a1b1c1-9999-4000-d000-111111111111",
  "override_ambulance_id": "a9b8c7d6-3333-4000-e000-999900001111",
  "override_hospital_id": "h1b2c3d4-2222-4000-f000-444455556666",
  "operator_id": "DISPATCHER_42",
  "override_reason": "Police requested immediate heavy rescue unit from Sector 4 due to tanker hazard."
}
```
* **Response (200 OK):** Confirms manual reassignment and records audit log.

---

## 6. PostgreSQL Database Schema (DDL)

```sql
-- PriorityCare PostgreSQL Relational Schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table 1: Hospitals
CREATE TABLE hospitals (
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
CREATE TABLE ambulances (
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
CREATE TABLE incidents (
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
CREATE TABLE call_reports (
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
CREATE TABLE assessment_answers (
    answer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(incident_id) ON DELETE CASCADE,
    call_id UUID NOT NULL REFERENCES call_reports(call_id) ON DELETE CASCADE,
    question_id VARCHAR(100) NOT NULL,
    selected_value VARCHAR(100) NOT NULL,
    raw_answer_text TEXT,
    answered_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Table 6: Priority Assessments Audit
CREATE TABLE priority_assessments (
    assessment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(incident_id) ON DELETE CASCADE,
    calculated_score INTEGER NOT NULL,
    assigned_tier VARCHAR(20) NOT NULL,
    rule_version VARCHAR(50) NOT NULL,
    contributing_factors TEXT[] NOT NULL DEFAULT '{}',
    is_instant_escalation BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Table 7: Dispatch Assignments (Automated Unit Assignments)
CREATE TABLE dispatch_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(incident_id) ON DELETE CASCADE,
    ambulance_id UUID NOT NULL REFERENCES ambulances(ambulance_id),
    hospital_id UUID NOT NULL REFERENCES hospitals(hospital_id),
    queue_priority_rank INTEGER NOT NULL DEFAULT 1,
    est_travel_seconds INTEGER NOT NULL,
    distance_to_scene_meters INTEGER NOT NULL,
    est_to_hospital_seconds INTEGER NOT NULL,
    distance_to_hospital_meters INTEGER NOT NULL,
    suitability_score NUMERIC(4, 2) NOT NULL,
    assignment_rationale TEXT NOT NULL,
    scene_route_geometry JSONB NOT NULL,
    hospital_route_geometry JSONB NOT NULL,
    is_overridden BOOLEAN NOT NULL DEFAULT FALSE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Table 8: Dispatch Actions (Operator Audit Trail)
CREATE TABLE dispatch_actions (
    action_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(incident_id),
    assignment_id UUID REFERENCES dispatch_assignments(assignment_id),
    ambulance_id UUID NOT NULL REFERENCES ambulances(ambulance_id),
    hospital_id UUID NOT NULL REFERENCES hospitals(hospital_id),
    operator_id VARCHAR(100) NOT NULL,
    action_type VARCHAR(50) NOT NULL DEFAULT 'AUTO_ASSIGN_ACK', -- AUTO_ASSIGN_ACK, MANUAL_OVERRIDE, REASSIGNMENT, CANCEL
    override_reason TEXT,
    action_timestamp TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Strategic Indexes for Sub-Millisecond Priority Queue & Spatial Lookup
CREATE INDEX idx_incidents_queue ON incidents(status, priority_tier, urgency_score DESC, created_at ASC);
CREATE INDEX idx_incidents_location ON incidents(latitude, longitude);
CREATE INDEX idx_ambulances_status ON ambulances(status, ambulance_type);
CREATE INDEX idx_calls_incident ON call_reports(incident_id);
```

---

## 7. Acceptance Criteria for Automated Assignment

1. **Scenario 1: Automated Queue-Based Assignment:**
   * Incident reaches `TRIAGED` or triggers instant P1.
   * **Verification:** System automatically assigns the closest suitable available ambulance using EST and marks incident `AUTO_ASSIGNED` / `DISPATCHED` with zero operator manual selection required.
2. **Scenario 2: Most Urgent Queue Preemption:**
   * Two incidents occur: Incident A is $P2$ (fracture), Incident B arrives as $P1$ (unconscious cardiac arrest).
   * **Verification:** Available ALS ambulance is automatically assigned to Incident B (Rank 1 in queue) regardless of which call started first.
3. **Scenario 3: Supervisory Override:**
   * Operator views the auto-assigned unit and clicks "Reassign Unit" with reason: *"Sector road impassable"*.
   * **Verification:** Reassignment succeeds, previous unit returns to `AVAILABLE`, new unit assigned, and `dispatch_actions` records the override reason.
