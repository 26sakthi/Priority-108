# PriorityCare (MEDI-DISPATCH AI) — Team Responsibilities, Ownership & Collaboration

**Document Version:** 1.1.0-RELEASE (Automatic Assignment Update)  
**Document Status:** Approved Team Governance & Ownership Agreement  
**Project:** PriorityCare (INTELLATHON '26 — Team JARVIS)  
**Cross-References:** Accompanies [PRD.md](file:///c:/Users/PURUSOUTHANAN/OneDrive/Desktop/priorcare/PRD.md), [SYSTEM_ARCHITECTURE.md](file:///c:/Users/PURUSOUTHANAN/OneDrive/Desktop/priorcare/SYSTEM_ARCHITECTURE.md), and [IMPLEMENTATION_PLAN.md](file:///c:/Users/PURUSOUTHANAN/OneDrive/Desktop/priorcare/IMPLEMENTATION_PLAN.md)  

---

## 1. Project Overview & Governance Philosophy

PriorityCare is an automated emergency dispatch and triage platform designed to assist 112/108 control-room operators handling acute medical emergencies and multi-casualty incidents. 

Delivering a cohesive, reliable system within hackathon constraints requires strict, non-overlapping ownership, transparent handoff gates, and disciplined contract adherence. Every contributor owns their deliverables from specification through unit testing.

```
┌────────────────────────────────────────────────────────────────────────┐
│                      FOUR-PILLAR OWNERSHIP MODEL                       │
├──────────────────┬───────────────────────────┬─────────────────────────┤
│ Contributor      │ Domain Specialization     │ Primary Code Location   │
├──────────────────┼───────────────────────────┼─────────────────────────┤
│ **Person 1**     │ AI, Architecture & DB     │ `app/services/routing/` │
│ (Product Lead /  │ Auto-Assignment, Routing, │ `app/services/auto_assign`
│ User)            │ PostgreSQL Schema & DDL   │ `app/models/`, `db/`    │
├──────────────────┼───────────────────────────┼─────────────────────────┤
│ **Person 2**     │ Clinical Decision Logic   │ `docs/TRIAGE_SPEC.md`   │
│ (Research Lead)  │ Vitals Tree & Scoring     │ `docs/QUESTION_BANK.json│
│                  │                           │ `tests/fixtures/`       │
├──────────────────┼───────────────────────────┼─────────────────────────┤
│ **Person 3**     │ Algorithm Implementation  │ `app/services/question/`│
│ (Integration)    │ Core Gateway & Master Git │ `app/services/priority/`│
│                  │                           │ `app/api/v1/`, `main.py`│
├──────────────────┼───────────────────────────┼─────────────────────────┤
│ **Person 4**     │ UI/UX & React Frontend    │ `frontend/src/`         │
│ (Frontend Lead)  │ Cockpit, Map & Overrides  │ `frontend/src/api/`     │
└──────────────────┴───────────────────────────┴─────────────────────────┘
```

---

## 2. Person 1 — AI, Architecture, Database and Auto-Assignment Owner

### 2.1 Primary Responsibility
Own the overall product requirements, technical system architecture, relational database schema and migrations, and the algorithmic **Automatic Ambulance Assignment** and Dijkstra hospital routing engines.

### 2.2 Tasks & Obligations
1. Maintain and govern [PRD.md](file:///c:/Users/PURUSOUTHANAN/OneDrive/Desktop/priorcare/PRD.md) and [SYSTEM_ARCHITECTURE.md](file:///c:/Users/PURUSOUTHANAN/OneDrive/Desktop/priorcare/SYSTEM_ARCHITECTURE.md).
2. Author and verify the PostgreSQL schema (`db/init.sql`) and SQLAlchemy ORM models (`app/models/`).
3. Define the frozen Pydantic domain models in `app/schemas/domain.py` ensuring contract consistency across frontend and backend.
4. Implement the **Automatic Ambulance Assignment Engine** (`app/services/auto_assignment_engine.py`):
   * Monitor the Dynamic Priority Queue and automatically match the most urgent incidents ($P1 > P2 > P3$).
   * Evaluate candidate ambulances by operational availability (`status == 'AVAILABLE'`) and clinical suitability (ALS for P1 trauma/cardiac, BLS for P2).
   * Calculate network Estimated Travel Time (EST / ETA) to scene using Dijkstra's shortest path over OpenStreetMap.
   * Automatically execute unit assignment without waiting for manual operator clicks.
5. Implement the Dijkstra Shortest-Route Graph Engine over OpenStreetMap (`app/services/routing_engine.py`), prioritizing clinically suitable and available receiving hospitals over mere proximity.
6. Provide a synthetic congestion multiplier model to simulate peak-hour traffic delays on road segments.
7. Implement resilient fallback mechanisms: if graph routing fails, fall back to Haversine Euclidean distance with urban detour penalties.
8. Seed the demo database (`db/seed_demo_data.py`) with realistic ambulances, regional hospitals, and road networks for the Perambalur / Trichy sector.
9. Write unit and property tests verifying automatic assignment, suitability scoring, and Dijkstra pathing (`tests/test_auto_assignment.py`, `tests/test_routing.py`).

### 2.3 Key Deliverables
* `PRD.md` and `SYSTEM_ARCHITECTURE.md`.
* `db/init.sql` and `app/models/`.
* `app/services/auto_assignment_engine.py` and `app/services/routing_engine.py`.
* Automated tests for auto-assignment, suitability scoring, and Dijkstra pathing.

### 2.4 Decision Boundaries & Authority
* **Absolute Authority:** PostgreSQL schema, database indexes, automatic assignment algorithm, EST calculation, and Dijkstra graph representation.
* **Collaboration Required:** Must coordinate with Person 3 for API route wiring and Person 4 for live assignment GeoJSON map rendering.
* **Boundary Constraint:** Must not independently alter clinical triage rules or claim medical validation without Person 2's research input.

---

## 3. Person 2 — Dynamic Question and Priority Research Owner

### 3.1 Primary Responsibility
Research, formalize, and document the clinical decision trees and deterministic scoring logic that govern emergency call intake and patient urgency triage.

### 3.2 Tasks & Obligations
1. Research and specify the 5 Essential Vitals intake sequence (Event, Consciousness, Respiration, Hemorrhage, Location) matching emergency standards.
2. Author the complete, executable question bank (`docs/QUESTION_BANK.json`) including question IDs, types, options, urgency weights, and branching conditions for Road Accidents and Cardiac/Unconscious modules.
3. Formalize the clinical scoring formula in `docs/TRIAGE_SPEC.md`, defining how symptom weights map to $P1$ (Critical), $P2$ (High Urgency), and $P3$ (Lower Urgency).
4. Specify the **Instant P1 Fail-Fast Rule**: ensure that absent breathing or massive uncontrolled bleeding triggers an immediate P1 alert in $<10$ seconds, immediately feeding into Person 1's Automatic Assignment Engine.
5. Define tie-breaking criteria (Urgency Tier $\to$ Urgency Score $\to$ Incident Creation Timestamp) and reassessment triggers when linked calls report updated symptoms.
6. Provide at least 5 concrete test scenarios with exact input payloads and expected score/tier outputs.

---

## 4. Person 3 — Algorithm Implementation and Integration Owner

### 4.1 Primary Responsibility
Translate approved clinical research and decision logic into performant backend services, build core API controllers, and serve as the **Master Branch Gatekeeper** for all codebase integration.

### 4.2 Tasks & Obligations
1. Implement the Dynamic Question Engine (`app/services/question_engine.py`) parsing Person 2's JSON decision graph.
2. Implement the Priority Scoring Engine (`app/services/priority_engine.py`) executing Person 2's formulas and triggering instant P1 alerts.
3. Implement the Spatial-Temporal Duplicate Detection Engine (`app/services/dedup_engine.py`) using bounding-box queries and multi-attribute confidence scoring ($<500$m, $<20$m).
4. Implement the Non-Destructive Merge logic: ensure duplicate call merges update casualty counts cumulatively ($\max(\text{reported}, \text{current})$).
5. Build and maintain FastAPI API routes (`app/api/v1/calls.py`, `app/api/v1/incidents.py`, `app/api/v1/dispatch.py`), wiring Person 1's Auto-Assignment Engine.
6. Author automated unit and contract tests (`tests/test_triage.py`, `tests/test_dedup.py`).
7. Manage the GitHub repository: review all pull requests, resolve merge conflicts, and prevent unverified code from reaching `master`.

---

## 5. Person 4 — UI/UX and React Frontend Owner

### 5.1 Primary Responsibility
Design and implement the high-impact, responsive React Single Page Application through which emergency dispatch operators interact with PriorityCare.

### 5.2 Tasks & Obligations
1. Create intuitive Figma designs for the 3-pane Operator Cockpit (Active Intake, Priority Queue, Leaflet Route Map).
2. Scaffold and maintain the React 18 / Vite application (`frontend/`).
3. Build the Dynamic Question Wizard (`CallIntakeModal.tsx`), rendering questions served from the backend and highlighting Instant P1 emergency warnings in bold red.
4. Build the Active Incident Queue (`IncidentQueue.tsx`), displaying live priority ranking ($P1$ Red, $P2$ Amber, $P3$ Green) with auto-assigned ambulance badges.
5. Build the Interactive Map Component (`MapView.tsx`) using Leaflet / OpenStreetMap, rendering incident markers, ambulance locations, and auto-dispatched GeoJSON route lines.
6. Build the Live Auto-Assignment Status Card (`AssignmentCard.tsx`), showing assigned ambulance, EST, receiving hospital, and route details.
7. Build the Manual Override Modal (`OverrideModal.tsx`) allowing the operator to supervise, reassign, or cancel the auto-assignment with an explicit reason code.
8. Connect React components to live FastAPI endpoints via an Axios/Fetch client (`frontend/src/api/client.ts`).

---

## 6. Shared Contract Ownership Matrix

| Functional Area | Primary Owner | Required Collaborators | Governance Rule |
| :--- | :---: | :---: | :--- |
| **Product Requirements & Scope** | Person 1 | All Contributors | Formally governed via `PRD.md`. |
| **System Architecture & Boundaries**| Person 1 | Person 3 & Person 4 | Formally governed via `SYSTEM_ARCHITECTURE.md`. |
| **PostgreSQL Schema & PostGIS DDL** | Person 1 | Person 3 | Changes require updating `db/init.sql` and SQLAlchemy models. |
| **Clinical Question Decision Tree** | Person 2 | Person 3 | Delivered via `docs/QUESTION_BANK.json`. |
| **Priority Scoring Formulas** | Person 2 | Person 3 & Person 1 | Delivered via `docs/TRIAGE_SPEC.md`. |
| **Triage & Dedup Implementation** | Person 3 | Person 2 | Must pass Person 2's scenario test cases. |
| **Automatic Ambulance Assignment** | Person 1 | Person 3 & Person 4 | Evaluates queue rank, location, availability & EST. |
| **React UI & Map Presentation** | Person 4 | Person 1 & Person 3 | Displays auto-assignments & override controls. |
| **Shared Pydantic Schemas** | Person 1 | All Affected Owners | **FROZEN.** Changes require unanimous consent. |
| **Master Branch Integration** | Person 3 | All Contributors | Person 3 has sole merge authority on `master`. |

---

## 7. Definition of Done (DoD)

A task or feature branch is declared **Done** if and only if:
1. **Contract Adherence:** Request and response bodies conform 100% to Pydantic models in `PRD.md`.
2. **Automated Verification:** Associated unit tests pass with zero errors.
3. **Graceful Error Handling:** Invalid inputs, missing locations, or database exceptions return standard error envelopes (`HTTP 4xx/5xx`) without unhandled crashes.
4. **Peer Review:** Code has been reviewed and merged into `master` by Person 3.
5. **No Regressions:** Existing end-to-end user workflows continue to operate cleanly on the integrated application.

---

### Team Agreement & Commitment
*Updated to reflect Automatic Ambulance Assignment by EST, Location Availability, and Priority Queue Ranking (Person 1).*
