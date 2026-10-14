# PriorityCare (MEDI-DISPATCH AI) — Complete Implementation Plan

**Document Version:** 1.1.0-RELEASE (Automatic Assignment Update)  
**Document Status:** Approved Engineering Roadmap Baseline  
**Project:** PriorityCare (INTELLATHON '26 — Team JARVIS)  
**Engineering Leads:** Senior Technical Project Manager, Software Architect & Engineering Lead (Person 1)  
**Cross-References:** Accompanies [PRD.md](file:///c:/Users/PURUSOUTHANAN/OneDrive/Desktop/priorcare/PRD.md), [SYSTEM_ARCHITECTURE.md](file:///c:/Users/PURUSOUTHANAN/OneDrive/Desktop/priorcare/SYSTEM_ARCHITECTURE.md), and [RESPONSIBILITY.md](file:///c:/Users/PURUSOUTHANAN/OneDrive/Desktop/priorcare/RESPONSIBILITY.md)  

---

## 1. Executive Implementation Strategy

PriorityCare is an emergency dispatch decision-support platform designed to transition 112/108 call-taking operations from slow, manual, proximity-based dispatch into an **automated, capability-aware copilot**.

### Core Evolution: Automatic Ambulance Assignment
Instead of presenting a list of recommended ambulances for manual operator selection, PriorityCare features an **Automatic Ambulance Assignment Engine** (developed by Person 1):
1. **Dynamic Priority Queue Ordering:** Active incidents are ordered by urgency tier ($P1 > P2 > P3$), urgency score, and wait time.
2. **Automated Matching:** For the highest-urgency unassigned queues, the engine automatically matches available ambulances (`status == 'AVAILABLE'`), checks clinical suitability (e.g. ALS with ventilator/defibrillator for P1), and computes network Estimated Travel Time (EST / ETA) via Dijkstra's algorithm over OpenStreetMap.
3. **Instant Auto-Dispatch:** The optimal unit is automatically assigned and dispatched without operator hesitation, while the operator retains supervisory override authority.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PARALLEL TRACK EXECUTION                        │
├─────────────────┬────────────────────────────┬─────────────────────────┤
│ Track A (AI/DB) │ Person 1: Auto-Assignment, │ Automatic Assignment &  │
│                 │ Dijkstra OSM, Schema & DDL │ routing engine          │
├─────────────────┼────────────────────────────┼─────────────────────────┤
│ Track B (Logic) │ Person 2: Question Trees,  │ Generates test fixtures │
│                 │ Scoring Formulas & Rubrics │ & clinical test cases   │
├─────────────────┼────────────────────────────┼─────────────────────────┤
│ Track C (Core)  │ Person 3: Question Engine, │ Builds FastAPI services │
│                 │ Priority, Dedup & Gateway  │ & maintains master      │
├─────────────────┼────────────────────────────┼─────────────────────────┤
│ Track D (UI/UX) │ Person 4: React Dashboard, │ Builds complete UI      │
│                 │ Leaflet OSM Map & Cockpit  │ against JSON mocks      │
└─────────────────┴────────────────────────────┴─────────────────────────┘
```

---

## 2. Team Roles and Ownership

| Role | Teammate | Core Focus Area | Primary Code & Artifact Ownership |
| :--- | :--- | :--- | :--- |
| **Person 1** | **Teammate A (Lead / User)** | **AI, Auto-Assignment & DB Architecture** | • `app/services/auto_assignment_engine.py`<br/>• `app/services/routing_engine.py` (Dijkstra on OSM)<br/>• `db/init.sql` & SQLAlchemy models (`app/models/`)<br/>• `PRD.md` & `SYSTEM_ARCHITECTURE.md` |
| **Person 2** | **Teammate B** | **Research & Decision Logic** | • `docs/TRIAGE_SPEC.md` (Clinical scoring rubric)<br/>• `docs/QUESTION_BANK.json` (Branching tree)<br/>• Scenario test cases & tie-breaking rules |
| **Person 3** | **Teammate C** | **Algorithm Implementation & Integration** | • `app/services/question_engine.py`<br/>• `app/services/priority_engine.py`<br/>• `app/services/dedup_engine.py`<br/>• `app/api/v1/` routes & master branch gateway |
| **Person 4** | **Teammate D** | **UI/UX & Frontend Development** | • React 18 / Vite SPA (`frontend/src/`)<br/>• Operator Cockpit (Queue, Question Wizard, Map)<br/>• Live Auto-Assignment & Leaflet visualization<br/>• Mock client & FastAPI API integration |

---

## 3. Master Task Matrix

| Task ID | Phase | Description | Owner | Support | Dependencies | Target Files / Modules | Deliverable | Acceptance Criteria | Priority | Status |
| :--- | :---: | :--- | :---: | :---: | :---: | :--- | :--- | :--- | :---: | :---: |
| **TSK-P0-01** | 0 | Schema & Contract Freeze | Person 1 | Person 3 | `PRD.md` | `app/schemas/domain.py` | Validated Pydantic models | Core entities & auto-assignment models locked | **P0** | **Done** |
| **TSK-P0-02** | 0 | Git Repo & Branch Rules | Person 3 | Person 1 | None | `.github/`, `.gitignore` | Branch protection on master | Feature branch strategy enforced | **P0** | **Done** |
| **TSK-P1-01** | 1 | Database DDL & Docker Compose | Person 1 | Person 3 | TSK-P0-01 | `db/init.sql`, `docker-compose.yml` | Running PostgreSQL container | Schema loads cleanly with foreign keys | **P0** | Not Started |
| **TSK-P1-02** | 1 | FastAPI Scaffold & CORS | Person 3 | Person 1 | TSK-P0-01 | `app/main.py`, `app/core/config.py` | FastAPI server with `/health` | Server boots and returns 200 OK | **P0** | Not Started |
| **TSK-P1-03** | 1 | React Scaffold & Leaflet Setup | Person 4 | Person 3 | None | `frontend/package.json`, `App.tsx` | Running React development server | Boots with 3-pane layout shell | **P0** | Not Started |
| **TSK-P1-04** | 1 | Mock JSON Fixtures for UI | Person 4 | Person 1 | TSK-P0-01 | `frontend/src/api/mockData.ts` | Static JSON responses matching PRD | UI renders mock queue, questions & map | **P0** | Not Started |
| **TSK-P2-01** | 2 | Clinical Triage Spec & Rules | Person 2 | Person 3 | TSK-P0-01 | `docs/TRIAGE_SPEC.md` | Triage scoring rubric & P1 triggers | Formulas documented with test examples | **P0** | Not Started |
| **TSK-P2-02** | 2 | Dynamic Question Bank JSON | Person 2 | Person 3 | TSK-P2-01 | `docs/QUESTION_BANK.json` | Decision tree for 5 vitals + RTA/Card | Valid JSON parsing into QuestionSchema | **P0** | Not Started |
| **TSK-P2-03** | 2 | Question Engine Service | Person 3 | Person 2 | TSK-P2-02 | `app/services/question_engine.py` | Dynamic branch evaluator service | Delivers next questions based on answers | **P0** | Not Started |
| **TSK-P2-04** | 2 | Priority Scoring Service | Person 3 | Person 2 | TSK-P2-01 | `app/services/priority_engine.py` | Urgency scoring calculation service | Absent breathing $\to$ P1 (<10s) verified | **P0** | Not Started |
| **TSK-P2-05** | 2 | OSM Road Graph Loader & Dijkstra | Person 1 | Person 3 | TSK-P0-01 | `app/services/routing_engine.py` | In-memory NetworkX routing engine | Dijkstra computes shortest path in <50ms | **P0** | Not Started |
| **TSK-P2-06** | 2 | Automatic Ambulance Assignment Engine | Person 1 | Person 3 | TSK-P0-01, TSK-P2-05 | `app/services/auto_assignment_engine.py`| Automated queue assignment service | Automatically assigns nearest suitable ALS/BLS by EST | **P0** | Not Started |
| **TSK-P2-07** | 2 | React Call Intake Wizard Component | Person 4 | Person 2 | TSK-P1-04 | `frontend/src/components/CallIntake.tsx` | Step-by-step 5-vitals question UI | Displays dynamic questions & handles P1 alert | **P0** | Not Started |
| **TSK-P2-08** | 2 | React Live Priority Queue Component| Person 4 | Person 3 | TSK-P1-04 | `frontend/src/components/IncidentQueue.tsx`| Table view sorted by P1/P2/P3 | Renders queue with auto-assigned unit badge | **P0** | Not Started |
| **TSK-P2-09** | 2 | React Leaflet Route Map Component | Person 4 | Person 1 | TSK-P1-04 | `frontend/src/components/MapView.tsx` | Map showing incidents, units & routes | Renders GeoJSON LineStrings on OSM | **P0** | Not Started |
| **TSK-P3-01** | 3 | Spatial-Temporal Dedup Engine | Person 3 | Person 1 | TSK-P1-01 | `app/services/dedup_engine.py` | Multi-factor clustering service | Clusters calls $\le 500$m & $\le 20$m | **P0** | Not Started |
| **TSK-P3-02** | 3 | Call Intake & Dedup API Routes | Person 3 | Person 1 | TSK-P3-01 | `app/api/v1/calls.py` | Endpoints: `/calls/intake`, `/answers` | Auto-detects duplicates and serves vitals | **P0** | Not Started |
| **TSK-P3-03** | 3 | Active Incident Queue API Route | Person 3 | Person 1 | TSK-P1-01 | `app/api/v1/incidents.py` | Endpoint: `GET /incidents?status=ACTIVE` | Returns SQL-sorted priority queue | **P0** | Not Started |
| **TSK-P3-04** | 3 | Auto-Assignment & Assignment API | Person 1 | Person 3 | TSK-P2-06 | `app/api/v1/dispatch.py` | Endpoints: `/dispatch/auto-assign`, `/assignment` | Triggers auto-assignment and returns EST route | **P0** | Not Started |
| **TSK-P3-05** | 3 | Dispatch Audit & Override Route | Person 1 | Person 3 | TSK-P1-01 | `app/api/v1/dispatch.py` | Endpoint: `POST /dispatch/override` | Records manual override with reason | **P0** | Not Started |
| **TSK-P3-06** | 3 | Demo Database Seed Script | Person 1 | Person 4 | TSK-P1-01 | `db/seed_demo_data.py` | Script seeding ambulances & hospitals | Seeds 10 ambulances & 5 hospitals | **P0** | Not Started |
| **TSK-P4-01** | 4 | Connect React to Live API Endpoints| Person 4 | Person 3 | TSK-P3-02 | `frontend/src/api/client.ts` | Axios client communicating with backend | Replaces mock fixtures with live API calls | **P0** | Not Started |
| **TSK-P4-02** | 4 | Real-Time Queue Auto-Refresh | Person 4 | Person 3 | TSK-P4-01 | `frontend/src/components/IncidentQueue.tsx`| Polling loop (every 3s) or refetch trigger | New auto-assignments appear immediately | **P0** | Not Started |
| **TSK-P4-03** | 4 | Live Assignment Display & Status | Person 4 | Person 1 | TSK-P3-04 | `frontend/src/components/AssignmentCard.tsx`| Shows auto-assigned unit, EST & hospital | Renders route automatically on map | **P0** | Not Started |
| **TSK-P4-04** | 4 | Manual Override Modal with Reason | Person 4 | Person 1 | TSK-P3-05 | `frontend/src/components/OverrideModal.tsx`| Modal capturing mandatory override reason | Submits override payload to backend | **P1** | Not Started |
| **TSK-P5-01** | 5 | End-to-End Automated Test Suite | Person 3 | Person 1 | TSK-P4-01 | `tests/test_e2e_workflow.py` | Pytest simulating full call-to-auto-dispatch| All operational scenarios pass | **P0** | Not Started |
| **TSK-P5-02** | 5 | Concurrency & Duplicate Merge Test | Person 3 | Person 2 | TSK-P3-01 | `tests/test_dedup_merge.py` | Test verifying casualty count accumulation | Call 1 (1 victim) + Call 2 (2 victims) $\to$ 2 | **P0** | Not Started |
| **TSK-P5-03** | 5 | Route Fallback on Map Error Test | Person 1 | Person 3 | TSK-P2-05 | `tests/test_routing_fallback.py` | Test verifying Haversine Euclidean fallback | Returns estimated route on broken graph | **P1** | Not Started |
| **TSK-P6-01** | 6 | 5-Minute Hackathon Demo Script | Person 1 | Person 2 | All | `docs/DEMO_SCRIPT.md` | Predictable 3-call judge presentation script | Step-by-step auto-dispatch script | **P0** | Not Started |
| **TSK-P6-02** | 6 | Synthetic Traffic Toggle Switch | Person 1 | Person 4 | TSK-P2-05 | `frontend/src/components/TrafficToggle.tsx`| UI switch simulating peak-hour congestion | Live EST dynamically increases with traffic | **P1** | Not Started |
| **TSK-P6-03** | 6 | Docker One-Click Launch Script | Person 1 | Person 3 | TSK-P1-01 | `docker-compose.yml`, `README.md` | `docker compose up` starts full stack | System initializes in $<90$ seconds | **P0** | Not Started |

---

## 4. Five-Minute Hackathon Demo Script (INTELLATHON '26)

```
[ Minute 0:00 - 0:45 ] THE PROBLEM & THE AUTOMATION INNOVATION
• Present the operator cockpit. Highlight the fatal flaw of conventional dispatch: operators manually browsing map pins while critical patients bleed out.
• Introduce PriorityCare's core AI feature: Automatic Ambulance Assignment for priority queues based on location, availability, and network EST.

[ Minute 0:45 - 2:00 ] CALL 1 & CALL 2 (Multi-Factor Deduplication & Casualty Invariant)
• Caller 1 reports a collision at Samayapuram Toll Plaza (1 injured). 
• Call 2 arrives 90 seconds later: bystander reports 2 injured trapped.
• SYSTEM ACTION: PriorityCare detects HIGH_MATCH (94% confidence). Merges call, updates casualty count to 2, and updates incident priority.

[ Minute 2:00 - 3:30 ] CALL 3 & AUTOMATIC DISPATCH EXECUTION
• Call 3 arrives: acute myocardial infarction (unconscious, not breathing).
• Operator marks "Absent Breathing" $\to$ Instant P1 Triggered in <10 seconds!
• SHOWCASE (THE WOW MOMENT): Zero operator clicks needed! The Automatic Assignment Engine instantly evaluates the priority queue, identifies Incident #103 as Rank 1, finds the nearest available ALS unit with ventilator (AMB-ALS-02), computes Dijkstra EST (6 mins), and automatically assigns and dispatches the unit!
• Map immediately animates the route to the patient, then to Hospital B (with active Cath Lab).

[ Minute 3:30 - 4:15 ] SUPERVISORY OVERRIDE DEMO
• Operator demonstrates supervisory control: clicks "Manual Override", inputs reason ("Police escort requesting alternative exit"), and reassigns unit to confirm human-in-the-loop auditability.

[ Minute 4:15 - 5:00 ] METRICS & SUSTAINABILITY IMPACT
• Show real-time telemetry: 45% reduction in dispatch latency, zero duplicate dispatches, 100% appropriate specialty hospital routing.
• Align with UN SDGs 3, 9, and 11.
```

---

### Implementation Plan Status
*Updated to reflect Automatic Ambulance Assignment by EST, Location Availability, and Priority Queue Ranking (Person 1).*
