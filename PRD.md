# PriorityCare (MEDI-DISPATCH AI) — Product Requirements Document (PRD) & Shared Data Contract

**Document Version:** 1.0.0-FINAL  
**Document Status:** Approved Data & API Contract Baseline  
**Project Repository:** PriorityCare (INTELLATHON '26 — Team JARVIS)  
**System Type:** Modular Monolith Emergency Dispatch Decision-Support System  
**Target Environment:** 112 / 108 Emergency Operations Control Center (Advisory Copilot)  

---

## 1. Document Overview & Team Ownership

This document establishes the single source of truth for PriorityCare's product requirements, domain entities, database schema, and REST API contract. All four team members must develop their modules against these interfaces to ensure zero-friction integration.

### 1.1 Team Roles & Modular Ownership Matrix

| Teammate | Focus Area | Specific Modular Ownership | Deliverable Responsibility |
| :--- | :--- | :--- | :--- |
| **Teammate A (Lead / User)** | **AI, Routing & Architecture** | • Ambulance allocation matching algorithm.<br/>• Hospital capability & Dijkstra routing engine.<br/>• System Architecture & PRD.<br/>• PostgreSQL schema & PostGIS queries. | • `app/services/allocation_engine.py`<br/>• `app/services/routing_engine.py`<br/>• `app/models/` (SQLAlchemy)<br/>• `db/init.sql` (PostgreSQL DDL) |
| **Teammate B** | **Research & Decision Logic** | • Dynamic clinical questioning decision trees.<br/>• P1/P2/P3 priority scoring formulas.<br/>• Clinical tie-breaking and escalation rules. | • `docs/TRIAGE_SPEC.md`<br/>• `docs/QUESTION_BANK.json`<br/>• Priority scoring weights & rubrics |
| **Teammate C** | **Backend Core & Integration** | • Dynamic question engine implementation.<br/>• Priority calculation service implementation.<br/>• Spatial-temporal duplicate detection.<br/>• FastAPI routes & master branch integration. | • `app/services/question_engine.py`<br/>• `app/services/priority_engine.py`<br/>• `app/services/dedup_engine.py`<br/>• `app/api/v1/` routes & tests |
| **Teammate D** | **UI/UX & Frontend** | • React Dispatcher Dashboard.<br/>• Live Priority Queue view.<br/>• Dynamic Question intake form.<br/>• Interactive OpenStreetMap (OSM) map view. | • `frontend/src/components/`<br/>• `frontend/src/api/client.ts`<br/>• Figma prototype & UI integration |

---

## 2. System Overview & Problem Statement

### 2.1 The Operational Bottleneck
Emergency call centres (such as 112/108) experience severe cognitive overload during multi-casualty incidents or call surges. Traditional workflows suffer from:
1. **Sequential Questioning Delays:** Rigid intake scripts delay dispatching units to unconscious or dying patients.
2. **Duplicate Call Chaos:** Multiple bystanders report the same crash, causing confusion or duplicate vehicle dispatches while other emergencies wait unserved.
3. **Casualty Count Dilution:** Naive deduplication wipes out critical updates (e.g., a 3rd caller reporting 2 trapped victims).
4. **Proximity-Only Dispatch:** Sending an ambulance based purely on straight-line distance without checking on-board equipment (ALS vs. BLS) or travel-time reality.
5. **Secondary Hospital Transfer Crisis:** Ambulances deliver patients to the nearest hospital only to find it lacks an open trauma ICU or cath lab.

### 2.2 The PriorityCare Solution
PriorityCare provides an automated **advisory copilot** for the call taker:
* **Adaptive Triage Intake:** A 5-question baseline with instant **P1 Fail-Fast Escalation** (if breathing/consciousness is absent, alert fires in $<10$ seconds).
* **Multi-Factor Duplicate Linking:** Links calls based on radius + time window + incident type, preserving cumulative casualty counts.
* **Capability-First Allocation:** Matches patient severity to ambulance equipment (ALS/BLS, ventilator, monitors) and road travel time.
* **Suitability-First Hospital Routing:** Uses Dijkstra’s shortest-path algorithm over an OpenStreetMap road graph to deliver patients directly to an appropriately equipped and available hospital.
* **Human-in-the-Loop Authority:** The operator approves or overrides every recommendation.

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
    DISPATCHING = "DISPATCHING"      # Recommendations generated, awaiting approval
    DISPATCHED = "DISPATCHED"        # Ambulance confirmed and en route
    ON_SCENE = "ON_SCENE"            # Ambulance arrived at incident location
    TRANSPORTING = "TRANSPORTING"    # En route to hospital
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
    ASSIGNED = "ASSIGNED"                # Selected by dispatcher, dispatch pending
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
| `active_ambulance_id` | UUID (string) | No | Reference to currently dispatched ambulance, if any. |
| `target_hospital_id` | UUID (string) | No | Reference to selected destination hospital, if any. |
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

### 4.8 Entity 7: Dispatch Recommendation (Advisory Proposal)
Generated by Teammate A's allocation and routing engines.

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `recommendation_id` | UUID (string) | Yes | Primary Key. |
| `incident_id` | UUID (string) | Yes | Incident being served. |
| `ambulance_id` | UUID (string) | Yes | Recommended vehicle. |
| `hospital_id` | UUID (string) | Yes | Recommended receiving hospital. |
| `eta_to_scene_seconds` | Integer | Yes | Estimated travel time to incident in seconds. |
| `distance_to_scene_meters`| Integer | Yes | Distance to incident in meters. |
| `eta_to_hospital_seconds`| Integer | Yes | Estimated travel time from incident to hospital in seconds. |
| `distance_to_hospital_meters`| Integer | Yes | Distance from incident to hospital in meters. |
| `suitability_match_score`| Float | Yes | Capability match score `(0.00 - 1.00)`. |
| `suitability_reason` | String | Yes | Human-readable rationale (e.g., `"ALS unit matched for cardiac arrest; Hospital B chosen for Cath Lab availability"`). |
| `scene_route_geometry` | GeoJSON LineString | Yes | Coordinates sequence for ambulance-to-incident path. |
| `hospital_route_geometry`| GeoJSON LineString | Yes | Coordinates sequence for incident-to-hospital path. |
| `is_selected` | Boolean | Yes | True if dispatcher confirmed this recommendation. |
| `created_at` | ISO 8601 UTC | Yes | Generation timestamp. |

---

### 4.9 Entity 8: DispatchAction (Audit Log)

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `action_id` | UUID (string) | Yes | Primary Key. |
| `incident_id` | UUID (string) | Yes | Target incident. |
| `recommendation_id` | UUID (string) | No | Associated recommendation if confirmed. |
| `ambulance_id` | UUID (string) | Yes | Dispatched ambulance. |
| `hospital_id` | UUID (string) | Yes | Destination hospital. |
| `operator_id` | String | Yes | Operator username or badge number. |
| `is_override` | Boolean | Yes | True if the operator rejected the system's top recommendation. |
| `override_reason` | String | No | Mandatory explanation if `is_override` is True. |
| `action_timestamp` | ISO 8601 UTC | Yes | Exact time confirmation was executed. |

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

Error response envelope:
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Incident with ID e2b83490-671b-4f7d-8157-1901b0f51234 was not found.",
    "details": null
  }
}
```

---

### 5.1 Call Intake & Dynamic Questioning API (Owned by Teammate C & B)

#### 1. Start Call Intake & Get Essential Questions
* **`POST /api/v1/calls/intake`**
* **Description:** Initiates a new emergency call session and returns the 5 essential screening questions.
* **Request Body:**
```json
{
  "caller_phone": "+919876543210",
  "caller_name": "Karthik Raja",
  "latitude": 11.234123,
  "longitude": 78.874123,
  "address_landmark": "NH-45 Samayapuram Toll Plaza",
  "initial_incident_type": "ROAD_TRAFFIC_ACCIDENT"
}
```
* **Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "call_id": "c1a2b3c4-0000-4000-a000-111122223333",
    "provisional_incident_id": "i9f8e7d6-1111-4000-b000-999988887777",
    "is_duplicate_detected": false,
    "questions": [
      {
        "question_id": "Q_EVENT_TYPE",
        "text": "What type of emergency occurred?",
        "question_type": "SINGLE_CHOICE",
        "options": [
          {"value": "ROAD_TRAFFIC_ACCIDENT", "label": "Vehicle Accident"},
          {"value": "CARDIAC_CHEST_PAIN", "label": "Chest Pain / Heart Attack"},
          {"value": "UNCONSCIOUS_FALL", "label": "Unconscious / Severe Fall"},
          {"value": "RESPIRATORY", "label": "Severe Breathing Difficulty"},
          {"value": "OTHER", "label": "Other Emergency"}
        ]
      },
      {
        "question_id": "Q_CONSCIOUSNESS",
        "text": "Is the patient conscious?",
        "question_type": "SINGLE_CHOICE",
        "options": [
          {"value": "ALERT", "label": "Alert and talking normally"},
          {"value": "DROWSY", "label": "Drowsy / Responds only to voice"},
          {"value": "UNRESPONSIVE", "label": "Completely unresponsive"}
        ]
      },
      {
        "question_id": "Q_BREATHING",
        "text": "Is the patient breathing normally?",
        "question_type": "SINGLE_CHOICE",
        "options": [
          {"value": "NORMAL", "label": "Normal breathing"},
          {"value": "DIFFICULT", "label": "Struggling to breathe / Agonal"},
          {"value": "ABSENT", "label": "NOT breathing / Gasping", "trigger_instant_p1": true}
        ]
      },
      {
        "question_id": "Q_BLEEDING",
        "text": "Is there severe, uncontrolled bleeding?",
        "question_type": "SINGLE_CHOICE",
        "options": [
          {"value": "NONE", "label": "No major bleeding"},
          {"value": "MODERATE", "label": "Controlled bleeding"},
          {"value": "SEVERE_PUMPING", "label": "Severe pumping / gushing blood"}
        ]
      },
      {
        "question_id": "Q_LOCATION_CONFIRM",
        "text": "Confirm exact accident spot / nearby milestone:",
        "question_type": "TEXT",
        "options": []
      }
    ]
  },
  "message": "Call intake initialized"
}
```

---

#### 2. Submit Answers & Evaluate Triage
* **`POST /api/v1/calls/{call_id}/answers`**
* **Description:** Submits operator-recorded answers. Evaluates priority immediately. If P1 conditions are met (e.g. absent breathing), returns instant escalation; otherwise returns follow-up adaptive questions.
* **Request Body:**
```json
{
  "answers": [
    {"question_id": "Q_EVENT_TYPE", "selected_value": "ROAD_TRAFFIC_ACCIDENT"},
    {"question_id": "Q_CONSCIOUSNESS", "selected_value": "UNRESPONSIVE"},
    {"question_id": "Q_BREATHING", "selected_value": "ABSENT"},
    {"question_id": "Q_BLEEDING", "selected_value": "SEVERE_PUMPING"}
  ]
}
```
* **Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "incident_id": "i9f8e7d6-1111-4000-b000-999988887777",
    "priority_tier": "P1_CRITICAL",
    "urgency_score": 98,
    "is_instant_p1_triggered": true,
    "escalation_reason": "Patient is unresponsive with absent breathing. Immediate P1 escalation engaged.",
    "is_triage_complete": false,
    "next_adaptive_questions": [
      {
        "question_id": "Q_RTA_CASUALTIES",
        "text": "How many total people are injured?",
        "question_type": "NUMERIC",
        "options": []
      },
      {
        "question_id": "Q_RTA_TRAPPED",
        "text": "Are any victims trapped inside vehicles?",
        "question_type": "SINGLE_CHOICE",
        "options": [
          {"value": "YES", "label": "Yes, trapped"},
          {"value": "NO", "label": "No, free"}
        ]
      },
      {
        "question_id": "Q_RTA_HAZARDS",
        "text": "Are there fire or fuel spill hazards?",
        "question_type": "MULTIPLE_CHOICE",
        "options": [
          {"value": "FUEL_LEAK", "label": "Fuel leaking on road"},
          {"value": "VEHICLE_FIRE", "label": "Vehicle on fire"},
          {"value": "HIGH_VOLTAGE", "label": "Fallen power lines"}
        ]
      }
    ]
  },
  "message": "Answers processed and priority assessed"
}
```

---

### 5.2 Duplicate Detection API (Owned by Teammate C & A)

#### 1. Check for Duplicate Incident
* **`POST /api/v1/incidents/check-duplicate`**
* **Description:** Analyzes whether an incoming call matches an active incident within spatial radius (e.g. 500m) and temporal window (e.g. 20 min).
* **Request Body:**
```json
{
  "latitude": 11.234180,
  "longitude": 78.874195,
  "incident_type": "ROAD_TRAFFIC_ACCIDENT",
  "landmark": "Near Samayapuram toll gate",
  "reported_casualties": 2
}
```
* **Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "match_confidence": "HIGH_MATCH",
    "confidence_score": 0.94,
    "matched_incident": {
      "incident_id": "i9f8e7d6-1111-4000-b000-999988887777",
      "incident_number": "INC-20261014-0012",
      "distance_meters": 32,
      "time_gap_seconds": 120,
      "current_casualty_count": 1,
      "projected_new_casualty_count": 2,
      "current_priority_tier": "P1_CRITICAL"
    },
    "recommendation": "AUTO_MERGE_SUGGESTED",
    "rationale": "Located 32m and 2 min apart from Incident INC-20261014-0012 with matching incident type."
  },
  "message": "Duplicate analysis complete"
}
```

#### 2. Confirm Call Merge to Existing Incident
* **`POST /api/v1/incidents/{incident_id}/merge-call`**
* **Description:** Merges a call into an existing incident, updating casualty count and appending details without overwriting existing data.
* **Request Body:**
```json
{
  "call_id": "c1a2b3c4-0000-4000-a000-111122223333",
  "updated_casualty_count": 2,
  "additional_notes": "Second caller confirms two persons injured; one on road, one trapped in car."
}
```
* **Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "incident_id": "i9f8e7d6-1111-4000-b000-999988887777",
    "incident_number": "INC-20261014-0012",
    "call_count": 2,
    "affected_casualty_count": 2,
    "updated_at": "2026-10-14T12:32:00Z"
  },
  "message": "Call successfully linked to incident"
}
```

---

### 5.3 Priority Queue & Incident Management API (Owned by Teammate C & D)

#### 1. Get Prioritized Incident Queue
* **`GET /api/v1/incidents?status=ACTIVE`**
* **Description:** Returns the live sorted queue of active incidents.
* **Ordering Logic:** `priority_tier` (P1 > P2 > P3), then `urgency_score` (descending), then `created_at` (ascending).
* **Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "total_active_incidents": 2,
    "queue": [
      {
        "incident_id": "i9f8e7d6-1111-4000-b000-999988887777",
        "incident_number": "INC-20261014-0012",
        "incident_type": "ROAD_TRAFFIC_ACCIDENT",
        "priority_tier": "P1_CRITICAL",
        "urgency_score": 98,
        "affected_casualty_count": 2,
        "status": "DISPATCHING",
        "address_landmark": "NH-45 Samayapuram Toll Plaza",
        "call_count": 2,
        "created_at": "2026-10-14T12:30:00Z",
        "assigned_ambulance": null
      },
      {
        "incident_id": "i3f4e5d6-2222-4000-c000-555544443333",
        "incident_number": "INC-20261014-0011",
        "incident_type": "CARDIAC_CHEST_PAIN",
        "priority_tier": "P2_HIGH_URGENCY",
        "urgency_score": 75,
        "affected_casualty_count": 1,
        "status": "DISPATCHED",
        "address_landmark": "New Bus Stand, Perambalur",
        "call_count": 1,
        "created_at": "2026-10-14T12:20:00Z",
        "assigned_ambulance": {
          "vehicle_code": "AMB-TN-04",
          "ambulance_type": "ALS"
        }
      }
    ]
  },
  "message": "Active incident queue retrieved"
}
```

---

### 5.4 Ambulance Allocation & Hospital Routing API (Owned by Teammate A)

#### 1. Get Dispatch Recommendations for Incident
* **`GET /api/v1/incidents/{incident_id}/recommendations`**
* **Description:** Runs the Allocation Engine and Dijkstra Hospital Routing Engine to return the top 3 ranked ambulance + hospital recommendations.
* **Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "incident_id": "i9f8e7d6-1111-4000-b000-999988887777",
    "incident_priority": "P1_CRITICAL",
    "recommendations": [
      {
        "recommendation_id": "r1a1b1c1-9999-4000-d000-111111111111",
        "rank": 1,
        "ambulance": {
          "ambulance_id": "a1b2c3d4-1111-4000-e000-111122223333",
          "vehicle_code": "AMB-ALS-02",
          "ambulance_type": "ALS",
          "base_station": "Trichy Medical College Depot",
          "staff": ["PARAMEDIC_ADVANCED", "VENTILATOR_CERTIFIED"],
          "equipment": ["DEFIBRILLATOR", "VENTILATOR", "TRAUMA_KIT"]
        },
        "eta_to_scene_seconds": 480,
        "distance_to_scene_meters": 4200,
        "receiving_hospital": {
          "hospital_id": "h1b2c3d4-2222-4000-f000-444455556666",
          "name": "Dhanalakshmi Srinivasan Medical College Hospital",
          "specialty_matched": "TRAUMA_LEVEL_1",
          "icu_beds_available": 3,
          "eta_to_hospital_seconds": 720,
          "distance_to_hospital_meters": 7800
        },
        "suitability_score": 0.96,
        "recommendation_rationale": "Rank 1: ALS Unit matched for P1 Severe Trauma. Hospital B selected over nearest Clinic A because Hospital B has active Level-1 Trauma ICU.",
        "scene_route": {
          "type": "LineString",
          "coordinates": [
            [78.854123, 11.214123],
            [78.864123, 11.224123],
            [78.874123, 11.234123]
          ]
        },
        "hospital_route": {
          "type": "LineString",
          "coordinates": [
            [78.874123, 11.234123],
            [78.884123, 11.244123],
            [78.894123, 11.254123]
          ]
        }
      }
    ]
  },
  "message": "Recommendations generated successfully"
}
```

---

#### 2. Confirm Dispatch (Operator Decision)
* **`POST /api/v1/dispatch/confirm`**
* **Description:** Operator confirms a system recommendation or applies a manual override. Transitions incident to `DISPATCHED` and ambulance to `EN_ROUTE_SCENE`.
* **Request Body:**
```json
{
  "incident_id": "i9f8e7d6-1111-4000-b000-999988887777",
  "recommendation_id": "r1a1b1c1-9999-4000-d000-111111111111",
  "ambulance_id": "a1b2c3d4-1111-4000-e000-111122223333",
  "hospital_id": "h1b2c3d4-2222-4000-f000-444455556666",
  "operator_id": "DISPATCHER_42",
  "is_override": false,
  "override_reason": null
}
```
* **Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "action_id": "d9e8f7a6-5555-4000-b000-333322221111",
    "incident_id": "i9f8e7d6-1111-4000-b000-999988887777",
    "incident_status": "DISPATCHED",
    "ambulance_code": "AMB-ALS-02",
    "ambulance_status": "EN_ROUTE_SCENE",
    "confirmed_hospital": "Dhanalakshmi Srinivasan Medical College Hospital",
    "dispatch_timestamp": "2026-10-14T12:35:10Z"
  },
  "message": "Ambulance successfully dispatched"
}
```

---

### 5.5 Fleet & Hospital Telemetry API (Owned by Teammate A & D)

#### 1. Get Live Ambulance Fleet Status
* **`GET /api/v1/ambulances`**
* **Response (200 OK):** Returns array of all ambulances with current coordinates, operational status, and equipment.

#### 2. Get Hospital Directory & Bed Status
* **`GET /api/v1/hospitals`**
* **Response (200 OK):** Returns array of hospitals, coordinates, available ICU beds, and emergency status.

---

## 6. Shared Pydantic V2 Schemas (`app/schemas/domain.py`)

All three backend teammates (A, B, C) can import these exact Pydantic models directly to avoid contract divergence:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class IncidentStatus(str, Enum):
    REPORTED = "REPORTED"
    TRIAGED = "TRIAGED"
    DISPATCHING = "DISPATCHING"
    DISPATCHED = "DISPATCHED"
    ON_SCENE = "ON_SCENE"
    TRANSPORTING = "TRANSPORTING"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"

class PriorityTier(str, Enum):
    P1_CRITICAL = "P1_CRITICAL"
    P2_HIGH_URGENCY = "P2_HIGH_URGENCY"
    P3_LOWER_URGENCY = "P3_LOWER_URGENCY"

class AmbulanceType(str, Enum):
    ALS = "ALS"
    BLS = "BLS"
    PTS = "PTS"

class AmbulanceStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    EN_ROUTE_SCENE = "EN_ROUTE_SCENE"
    AT_SCENE = "AT_SCENE"
    EN_ROUTE_HOSPITAL = "EN_ROUTE_HOSPITAL"
    AT_HOSPITAL = "AT_HOSPITAL"
    MAINTENANCE = "MAINTENANCE"

class MatchConfidence(str, Enum):
    HIGH_MATCH = "HIGH_MATCH"
    UNCERTAIN_MATCH = "UNCERTAIN_MATCH"
    NO_MATCH = "NO_MATCH"

class GeoLocation(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

class CallIntakeRequest(BaseModel):
    caller_phone: str
    caller_name: Optional[str] = None
    latitude: float
    longitude: float
    address_landmark: str
    initial_incident_type: str

class QuestionOption(BaseModel):
    value: str
    label: str
    urgency_weight: int = 0
    trigger_instant_p1: bool = False

class QuestionSchema(BaseModel):
    question_id: str
    text: str
    question_type: str
    options: List[QuestionOption] = []

class AnswerSubmission(BaseModel):
    question_id: str
    selected_value: str
    raw_text: Optional[str] = None

class AnswersPayload(BaseModel):
    answers: List[AnswerSubmission]

class TriageEvaluationResponse(BaseModel):
    incident_id: UUID
    priority_tier: PriorityTier
    urgency_score: int
    is_instant_p1_triggered: bool
    escalation_reason: Optional[str]
    is_triage_complete: bool
    next_adaptive_questions: List[QuestionSchema] = []

class DuplicateCheckRequest(BaseModel):
    latitude: float
    longitude: float
    incident_type: str
    landmark: Optional[str] = None
    reported_casualties: int = 1

class DispatchConfirmRequest(BaseModel):
    incident_id: UUID
    recommendation_id: Optional[UUID] = None
    ambulance_id: UUID
    hospital_id: UUID
    operator_id: str
    is_override: bool = False
    override_reason: Optional[str] = None
```

---

## 7. PostgreSQL Database Schema (DDL)

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

-- Table 7: Dispatch Recommendations
CREATE TABLE dispatch_recommendations (
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
CREATE TABLE dispatch_actions (
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

-- Strategic Indexes for Sub-Millisecond Priority Queue & Spatial Lookup
CREATE INDEX idx_incidents_queue ON incidents(status, priority_tier, urgency_score DESC, created_at ASC);
CREATE INDEX idx_incidents_location ON incidents(latitude, longitude);
CREATE INDEX idx_ambulances_status ON ambulances(status, ambulance_type);
CREATE INDEX idx_calls_incident ON call_reports(incident_id);
```

---

## 8. Git Branching Strategy & Parallel Workflow

To allow all four team members to work without merge conflicts, the following branch and integration plan is enforced:

```
               [ master ] (Protected: Maintained by Teammate C)
                   │
    ┌──────────────┼──────────────┬──────────────┐
    ▼              ▼              ▼              ▼
feature/ai-    feature/       feature/       feature/
allocation-    triage-rules   backend-core   react-ui
routing        (Teammate B)   (Teammate C)   (Teammate D)
(Teammate A)
```

1. **Contract Freeze:** The schema and OpenAPI endpoints defined in this document are **frozen**. No teammate may alter field names or types without a team consultation.
2. **Mocking for Frontend (Teammate D):** A lightweight FastAPI mock server or static JSON fixtures matching Section 5 will allow Teammate D to build the complete React UI immediately, without waiting for the backend engines.
3. **Pull Request Protocol:**
   * Teammate B delivers JSON question trees and scoring rules to Teammate C.
   * Teammate C implements the question and priority engines in `app/services/`.
   * Teammate A implements the allocation and Dijkstra routing engines in `app/services/`.
   * All merges into `master` require verifying that request/response payloads match this PRD document.

---

## 9. Verification & Hackathon Acceptance Criteria

The system will be declared demo-ready when the following end-to-end user scenario passes:

1. **Scenario 1: Call Intake & Instant P1 Escalation:**
   * Incoming call with `Q_BREATHING = ABSENT`.
   * **Verification:** Priority immediately reports `P1_CRITICAL` and `urgency_score >= 95` within 1 API request.
2. **Scenario 2: Duplicate Incident Merging:**
   * Call 1 reports accident at Toll Plaza (1 victim).
   * Call 2 reports same accident 150m away within 3 minutes (reports 2 victims).
   * **Verification:** Call 2 is matched as `HIGH_MATCH` to Incident 1. Casualties update to 2. No second incident is created.
3. **Scenario 3: Suitability-First Routing:**
   * Severe trauma incident.
   * Hospital A is 8 minutes away but lacks Trauma ICU.
   * Hospital B is 14 minutes away with active Trauma ICU.
   * **Verification:** System recommends Hospital B with explanation: *"Hospital B selected over nearest Clinic A due to Trauma Level-1 requirement."*
4. **Scenario 4: Dispatch Confirmation & Audit Log:**
   * Operator clicks confirm.
   * **Verification:** Incident moves to `DISPATCHED`, ambulance moves to `EN_ROUTE_SCENE`, and `dispatch_actions` records the operator ID.
