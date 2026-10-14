# PriorityCare (MEDI-DISPATCH AI) — Team Responsibilities, Ownership & Collaboration

**Document Version:** 1.0.0-RELEASE  
**Document Status:** Approved Team Governance & Ownership Agreement  
**Project:** PriorityCare (INTELLATHON '26 — Team JARVIS)  
**Cross-References:** Accompanies [PRD.md](file:///c:/Users/PURUSOUTHANAN/OneDrive/Desktop/priorcare/PRD.md), [SYSTEM_ARCHITECTURE.md](file:///c:/Users/PURUSOUTHANAN/OneDrive/Desktop/priorcare/SYSTEM_ARCHITECTURE.md), and [IMPLEMENTATION_PLAN.md](file:///c:/Users/PURUSOUTHANAN/OneDrive/Desktop/priorcare/IMPLEMENTATION_PLAN.md)  

---

## 1. Project Overview & Governance Philosophy

PriorityCare is an emergency dispatch decision-support platform designed to assist 112/108 control-room operators handling acute medical emergencies and multi-casualty incidents. 

Delivering a cohesive, reliable system within hackathon constraints requires strict, non-overlapping ownership, transparent handoff gates, and disciplined contract adherence. No team member is an island, yet no team member is the default fixer for another's unfinished tasks. Every contributor owns their deliverables from specification through unit testing.

```
┌────────────────────────────────────────────────────────────────────────┐
│                      FOUR-PILLAR OWNERSHIP MODEL                       │
├──────────────────┬───────────────────────────┬─────────────────────────┤
│ Contributor      │ Domain Specialization     │ Primary Code Location   │
├──────────────────┼───────────────────────────┼─────────────────────────┤
│ **Person 1**     │ AI, Architecture & DB     │ `app/services/routing/` │
│ (Product Lead)   │ Allocation, Routing & DDL │ `app/services/alloc/`   │
│                  │                           │ `app/models/`, `db/`    │
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
│ (Frontend Lead)  │ Cockpit, Map & Workflows  │ `frontend/src/api/`     │
└──────────────────┴───────────────────────────┴─────────────────────────┘
```

---

## 2. Person 1 — AI, Architecture and Database Owner

### 2.1 Primary Responsibility
Own the overall product requirements, technical system architecture, relational database schema and migrations, and the algorithmic recommendation and routing engines.

### 2.2 Tasks & Obligations
1. Maintain and govern [PRD.md](file:///c:/Users/PURUSOUTHANAN/OneDrive/Desktop/priorcare/PRD.md) and [SYSTEM_ARCHITECTURE.md](file:///c:/Users/PURUSOUTHANAN/OneDrive/Desktop/priorcare/SYSTEM_ARCHITECTURE.md).
2. Author and verify the PostgreSQL schema (`db/init.sql`) and SQLAlchemy ORM models (`app/models/`).
3. Define the frozen Pydantic domain models in `app/schemas/domain.py` ensuring contract consistency across frontend and backend.
4. Implement the capability-aware Ambulance Allocation Engine (`app/services/allocation_engine.py`), matching incident severity against vehicle types (ALS vs. BLS), kit, and crew skills.
5. Implement the Dijkstra Shortest-Route Graph Engine over OpenStreetMap (`app/services/routing_engine.py`), prioritizing clinically suitable and available receiving hospitals over mere proximity.
6. Provide a synthetic congestion multiplier model to simulate peak-hour traffic delays on road segments.
7. Implement resilient fallback mechanisms: if graph routing fails, fall back to Haversine Euclidean distance with urban detour penalties.
8. Seed the demo database (`db/seed_demo_data.py`) with realistic ambulances, regional hospitals, and road networks for the Perambalur / Trichy sector.
9. Write unit and property tests verifying allocation and routing behavior (`tests/test_allocation.py`, `tests/test_routing.py`).

### 2.3 Key Deliverables
* `PRD.md` and `SYSTEM_ARCHITECTURE.md`.
* `db/init.sql` and `app/models/`.
* `app/services/allocation_engine.py` and `app/services/routing_engine.py`.
* Automated tests for allocation, suitability scoring, and Dijkstra pathing.

### 2.4 Decision Boundaries & Authority
* **Absolute Authority:** PostgreSQL schema, database indexes, allocation matching weights, and Dijkstra graph representation.
* **Collaboration Required:** Must coordinate with Person 3 for API route wiring and Person 4 for GeoJSON map payload visualization.
* **Boundary Constraint:** Must not independently alter clinical triage rules or claim medical validation without Person 2's research input.

---

## 3. Person 2 — Dynamic Question and Priority Research Owner

### 3.1 Primary Responsibility
Research, formalize, and document the clinical decision trees and deterministic scoring logic that govern emergency call intake and patient urgency triage.

### 3.2 Tasks & Obligations
1. Research and specify the 5 Essential Vitals intake sequence (Event, Consciousness, Respiration, Hemorrhage, Location) matching emergency standards (e.g., MPDS / NHS Pathways principles adapted for India's 112/108).
2. Author the complete, executable question bank (`docs/QUESTION_BANK.json`) including question IDs, types, options, urgency weights, and branching conditions for Road Accidents and Cardiac/Unconscious modules.
3. Formalize the clinical scoring formula in `docs/TRIAGE_SPEC.md`, defining how symptom weights map to $P1$ (Critical), $P2$ (High Urgency), and $P3$ (Lower Urgency).
4. Specify the **Instant P1 Fail-Fast Rule**: ensure that absent breathing or massive uncontrolled bleeding triggers an immediate P1 alert in $<10$ seconds, bypassing secondary questions.
5. Define tie-breaking criteria (Urgency Tier $\to$ Urgency Score $\to$ Incident Creation Timestamp) and reassessment triggers when linked calls report updated symptoms.
6. Provide at least 5 concrete test scenarios with exact input payloads and expected score/tier outputs.
7. Identify and document assumptions, explicitly acknowledging that this prototype triage logic requires clinical trials before real 108 deployment.

### 3.3 Key Deliverables
* `docs/TRIAGE_SPEC.md` (Clinical rubric, scoring math, and tie-breaking rules).
* `docs/QUESTION_BANK.json` (Structured decision tree and option schema).
* `tests/fixtures/triage_scenarios.json` (Executable test cases with expected outputs).

### 3.4 Decision Boundaries & Authority
* **Absolute Authority:** Triage score rubrics, vital sign weighting, adaptive branching logic, and clinical tie-breaking rules.
* **Collaboration Required:** Must coordinate with Person 3 to ensure questions and options serialize cleanly into `QuestionSchema` and `AnswersPayload`.
* **Boundary Constraint:** Person 2 owns research and specification; Person 2 does not commit application code directly to backend API routes or alter database tables without coordination.

### 3.5 Handoff Requirement to Person 3
Person 2 must deliver **testable, implementation-ready specifications** (in JSON and Markdown format with explicit inputs and expected outputs). Person 3 must never be forced to guess mathematical weights or branching conditions.

---

## 4. Person 3 — Algorithm Implementation and Integration Owner

### 4.1 Primary Responsibility
Translate approved clinical research and decision logic into performant backend services, build core API controllers, and serve as the **Master Branch Gatekeeper** for all codebase integration.

### 4.2 Tasks & Obligations
1. Implement the Dynamic Question Engine (`app/services/question_engine.py`) parsing Person 2's JSON decision graph and serving next questions dynamically.
2. Implement the Priority Scoring Engine (`app/services/priority_engine.py`) executing Person 2's formulas and triggering instant P1 alerts.
3. Implement the Spatial-Temporal Duplicate Detection Engine (`app/services/dedup_engine.py`) using bounding-box queries and multi-attribute confidence scoring ($<500$m, $<20$m).
4. Implement the Non-Destructive Merge logic: ensure duplicate call merges update casualty counts cumulatively ($\max(\text{reported}, \text{current})$).
5. Build and maintain FastAPI API routes (`app/api/v1/calls.py`, `app/api/v1/incidents.py`, `app/api/v1/dispatch.py`).
6. Enforce request/response validation against Pydantic models from `app/schemas/domain.py`.
7. Author automated unit and contract tests (`tests/test_triage.py`, `tests/test_dedup.py`).
8. Manage the GitHub repository: review all pull requests, resolve merge conflicts, and prevent unverified code from reaching `master`.
9. Enforce the Definition of Done on all incoming pull requests.

### 4.3 Key Deliverables
* `app/services/question_engine.py`, `app/services/priority_engine.py`, and `app/services/dedup_engine.py`.
* `app/api/v1/` route controllers and FastAPI server entrypoint (`app/main.py`).
* Automated unit, contract, and integration test suites (`pytest tests/`).
* A stable, green, deployable `master` branch.

### 4.4 Decision Boundaries & Authority
* **Absolute Authority:** Pull request approval/rejection on `master`, code formatting standards, internal backend service structure, and test execution policies.
* **Boundary Constraint:** Person 3 is **NOT the default implementer** of other teammates' unfinished tasks. If an AI module or frontend component fails tests, the original author (Person 1 or Person 4) must debug and repair it. Person 3 preserves architecture integrity and coordinates integration.

---

## 5. Person 4 — UI/UX and React Frontend Owner

### 5.1 Primary Responsibility
Design and implement the high-impact, responsive React Single Page Application through which emergency dispatch operators interact with PriorityCare.

### 5.2 Tasks & Obligations
1. Create intuitive Figma designs for the 3-pane Operator Cockpit (Active Intake, Priority Queue, Leaflet Route Map).
2. Scaffold and maintain the React 18 / Vite application (`frontend/`).
3. Build the Dynamic Question Wizard (`CallIntakeModal.tsx`), rendering questions served from the backend and highlighting Instant P1 emergency warnings in bold red.
4. Build the Active Incident Queue (`IncidentQueue.tsx`), rendering cards color-coded by urgency ($P1$ Red, $P2$ Amber, $P3$ Green) with auto-refresh polling.
5. Build the Interactive Map Component (`MapView.tsx`) using Leaflet / OpenStreetMap, rendering incident markers, ambulance icons, and GeoJSON route lines.
6. Build the Recommendation Proposal Card (`RecommendationCard.tsx`), showing ambulance ETA, equipment match, receiving hospital, and the one-click "Confirm Dispatch" action.
7. Build the Manual Override Modal (`OverrideModal.tsx`) requiring the operator to submit an explicit reason code if rejecting the system recommendation.
8. Create and maintain static mock fixtures (`frontend/src/api/mockData.ts`) matching `PRD.md` so UI development proceeds without waiting for backend readiness.
9. Connect React components to live FastAPI endpoints via an Axios/Fetch client (`frontend/src/api/client.ts`).
10. Implement resilient UI states: Loading skeletons, Error toast notifications, Stale-data indicators, and Empty queue states.

### 5.3 Key Deliverables
* Figma design system and component mockups.
* React 18 production build (`frontend/src/`).
* Interactive Leaflet map visualizer with dynamic GeoJSON rendering.
* Connected, end-to-end validated frontend operating against live FastAPI endpoints.

### 5.4 Decision Boundaries & Authority
* **Absolute Authority:** Visual layout, typography, UI component hierarchy, color palettes, micro-animations, and client-side state management.
* **Boundary Constraint:** Must strictly adhere to `snake_case` JSON field names defined in `PRD.md`. Person 4 must not invent arbitrary field names (e.g., using `patientCount` instead of `affected_casualty_count`) or alter enum values client-side.

---

## 6. Shared Responsibilities & Ethical Commitments

All four contributors commit to the following principles:

1. **System Understanding:** Every contributor must understand the complete 8-stage operational workflow from incoming call to hospital delivery.
2. **Contract Discipline:** Zero tolerance for unilateral schema drift. All JSON payloads must match `app/schemas/domain.py`.
3. **Immediate Blocker Escalation:** If a dependency or contract issue blocks progress for $>30$ minutes, it must be reported to the team immediately.
4. **No Direct Master Pushes:** All work must originate on assigned feature branches.
5. **No Secrets in Code:** Passwords, API tokens, and database credentials must reside strictly in `.env` files and `.gitignore`.
6. **Hackathon Integrity & Regulatory Realism:** All team members agree that PriorityCare is a hackathon decision-support prototype. In all presentations, code comments, and documentation, the team will explicitly state that clinical triage rules require formal medical validation and state authorization before real 112/108 deployment.

---

## 7. Shared Contract Ownership Matrix

| Functional Area | Primary Owner | Required Collaborators | Governance Rule |
| :--- | :---: | :---: | :--- |
| **Product Requirements & Scope** | Person 1 | All Contributors | Formally governed via `PRD.md`. |
| **System Architecture & Boundaries**| Person 1 | Person 3 & Person 4 | Formally governed via `SYSTEM_ARCHITECTURE.md`. |
| **PostgreSQL Schema & PostGIS DDL** | Person 1 | Person 3 | Changes require updating `db/init.sql` and SQLAlchemy models. |
| **Clinical Question Decision Tree** | Person 2 | Person 3 | Delivered via `docs/QUESTION_BANK.json`. |
| **Priority Scoring Formulas** | Person 2 | Person 3 & Person 1 | Delivered via `docs/TRIAGE_SPEC.md`. |
| **Triage & Dedup Implementation** | Person 3 | Person 2 | Must pass Person 2's scenario test cases. |
| **Allocation & Routing Engines** | Person 1 | Person 3 & Person 4 | Must emit valid GeoJSON LineStrings for UI rendering. |
| **React UI & Map Presentation** | Person 4 | Person 1 & Person 3 | Must consume frozen REST schemas directly. |
| **Shared Pydantic Schemas** | Person 1 | All Affected Owners | **FROZEN.** Changes require unanimous consent. |
| **Master Branch Integration** | Person 3 | All Contributors | Person 3 has sole merge authority on `master`. |
| **End-to-End Demo Validation** | All | Person 3 (Coordinator) | All 4 members verify the 5-minute hackathon demo. |

---

## 8. GitHub Branching and Pull Request Policy

```
                  [ master ] (Protected Branch)
                       │
         ┌─────────────┼─────────────┬─────────────┐
         ▼             ▼             ▼             ▼
      feature/      feature/      feature/      feature/
      ai-routing    triage-logic  backend-core  react-ui
     (Person 1)    (Person 2)    (Person 3)    (Person 4)
```

### 8.1 Branch Naming Conventions
* `feature/ai-allocation-routing` (Person 1)
* `feature/triage-research-rules` (Person 2)
* `feature/backend-api-core` (Person 3)
* `feature/react-operator-ui` (Person 4)
* `fix/<issue-description>` (For bug fixes during Phase 5 validation)

### 8.2 Pull Request Checklist
Before requesting a review from Person 3, the pull request author must verify:
- [ ] Branch is rebased onto latest `origin/master` (`git pull --rebase origin master`).
- [ ] Code passes formatting and linting checks.
- [ ] Automated unit tests pass locally (`pytest tests/`).
- [ ] No unauthorized changes were made to `app/schemas/domain.py`.
- [ ] Pull request description details: (a) what was built, (b) how to verify it, (c) screenshots if UI.

### 8.3 Emergency Hotfix Policy
If an integration defect blocks testing during Phase 5 or 6, Person 3 and the respective module owner will pair-program on the fix and push a joint commit directly to `master` with the prefix `[HOTFIX]`.

---

## 9. Communication, Handoff Protocols & Blocker Management

### 9.1 Daily 10-Minute Standup Protocol
Conducted twice daily (morning alignment and evening checkpoint):
1. **Accomplishments:** What did I finish since the last sync?
2. **Commitments:** What will I complete and push before the next sync?
3. **Blockers:** What is impeding my progress (contract ambiguity, broken API, missing fixture)?

### 9.2 Structured Handoff Protocols
* **Person 2 $\to$ Person 3 Handoff:** Person 2 delivers `docs/QUESTION_BANK.json` and `docs/TRIAGE_SPEC.md` accompanied by 5 executable JSON input/output test cases.
* **Person 1 $\to$ Person 3 Handoff:** Person 1 delivers `allocation_engine.py` and `routing_engine.py` accompanied by unit tests showing successful Dijkstra path computation and candidate ranking.
* **Person 3 $\to$ Person 4 Handoff:** Person 3 notifies Person 4 that an API endpoint is live on `master`, providing the Swagger UI link (`http://localhost:8000/docs`) for validation.
* **Person 4 $\to$ Person 1 & 3 Change Request:** If the frontend requires an additional field, Person 4 submits a formal request specifying: (a) the user interaction requiring it, and (b) the proposed field name in `snake_case`.

---

## 10. Definition of Done (DoD)

A task or feature branch is declared **Done** if and only if all of the following conditions are met:
1. **Contract Adherence:** Request and response bodies conform 100% to Pydantic models in `PRD.md`.
2. **Automated Verification:** Associated unit tests pass with zero errors.
3. **Graceful Error Handling:** Invalid inputs, missing locations, or database exceptions return standard error envelopes (`HTTP 4xx/5xx`) without unhandled crashes.
4. **Peer Review:** Code has been reviewed and merged into `master` by Person 3.
5. **No Regressions:** Existing end-to-end user workflows continue to operate cleanly on the integrated application.

---

### Team Agreement & Commitment
*By committing to this document, all four team members accept their roles, deliverables, and boundaries to ensure the unified delivery of PriorityCare at INTELLATHON '26.*
