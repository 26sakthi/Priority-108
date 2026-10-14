# PriorityCare (MEDI-DISPATCH AI) 🚑🚨

> **INTELLATHON '26 (DSIRT × Dongguk University) — Team JARVIS**  
> **Target Environment:** 112 ERSS & 108 Medical Emergency Operations Control Center (Advisory Copilot)  
> **System Architecture:** Modular Monolith (FastAPI + PostgreSQL/SQLite + NetworkX Dijkstra Routing + React 18 & Leaflet)

---

## 🌟 Executive Overview

PriorityCare transitions emergency operations from slow, manual, proximity-based dispatch into an **automated, clinical-capability-aware advisory copilot**:

1. **Adaptive Triage Intake:** 5-question baseline with **Instant P1 Fail-Fast Escalation** (if breathing/consciousness is absent, alert fires in $<10$ seconds, bypassing secondary questions).
2. **Multi-Factor Duplicate Linking:** Links concurrent bystander calls within 500m & 20 min using spatial-temporal clustering while strictly **preserving cumulative casualty counts**.
3. **Capability-First Allocation:** Evaluates ambulance suitability (ALS vs BLS, ventilator, defibrillator) alongside network road transit times.
4. **Suitability-First Hospital Routing:** Uses Dijkstra’s shortest-path algorithm over the OpenStreetMap road graph, prioritizing hospitals with active trauma ICUs and open beds over closer, ill-equipped clinics.
5. **Human-in-the-Loop Authority:** The human dispatcher reviews, confirms, or overrides every AI proposal with an immutable audit log.

---

## 🏗️ System Architecture

```
prioritycare/
├── app/
│   ├── api/v1/                   # REST Routes (calls, incidents, dispatch, telemetry)
│   ├── core/                     # App settings & error envelopes
│   ├── models/                   # SQLAlchemy database ORM models
│   ├── schemas/                  # Pydantic V2 frozen contracts
│   └── services/                 # 5 Core Domain Engines:
│       ├── question_engine.py    # Dynamic screening & adaptive branching
│       ├── priority_engine.py    # Triage scoring & instant P1 fail-fast
│       ├── dedup_engine.py       # Spatial-temporal call clustering (500m, 20m)
│       ├── routing_engine.py     # Dijkstra shortest-path on OSM road graph
│       └── allocation_engine.py  # Capability-first ambulance ranking
├── db/
│   ├── database.py               # Engine & session management
│   ├── init.sql                  # PostgreSQL & PostGIS DDL schema
│   └── seed_demo_data.py         # Seeded regional ambulances & hospitals
├── docs/
│   ├── PRD.md                    # Product Requirements Document
│   ├── SYSTEM_ARCHITECTURE.md    # Complete C4 System Architecture
│   ├── IMPLEMENTATION PLAN.md    # Engineering Roadmap
│   ├── TRIAGE_SPEC.md            # Clinical Scoring Protocol
│   ├── QUESTION_BANK.json        # Dynamic Decision Tree
│   └── DEMO_SCRIPT.md            # 5-Minute Judge Presentation Script
├── frontend/                     # React 18 + Vite + Leaflet Cockpit
│   ├── src/components/           # Live Queue, Recommendation Card, Map, Modals
│   └── src/api/client.ts         # REST API Client
├── tests/                        # 13 Automated Pytest Suites
├── docker-compose.yml            # Multi-container deployment
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Run Backend Server (FastAPI)
```bash
# Python 3.10+ (SQLite zero-setup database included)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
* **API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

### 2. Run Frontend Dashboard (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
* **Operator Cockpit:** [http://localhost:5173](http://localhost:5173)

### 3. Run Automated Tests
```bash
python -m pytest tests/ -v
```
*(All 13 unit & end-to-end integration tests execute in ~2 seconds).*

---

## 🧪 4 Acceptance Scenarios Verified

| Scenario | Objective | Verification Outcome |
| :--- | :--- | :--- |
| **1. Instant P1 Escalation** | `Q_BREATHING = ABSENT` input | Triage immediately reports `P1_CRITICAL` and score $\ge 95$ in $<10$s. |
| **2. Duplicate Merging** | Call 2 arrives 35m away within 3 mins reporting 3 victims | Matched as `HIGH_MATCH`, casualty count increases to 3 without ghost incidents. |
| **3. Suitability-First Routing** | Severe trauma patient | System routes to Dhanalakshmi Srinivasan Medical College Hospital (with Trauma Level-1 ICU) over closer clinic. |
| **4. Dispatch Confirmation** | Operator clicks Confirm | Incident moves to `DISPATCHED`, ambulance updates to `EN_ROUTE_SCENE`, audit logged. |

---

## 👥 Team JARVIS Roles
* **Person 1 (Lead / User):** AI, Routing & Architecture (Allocation Engine, Dijkstra OSM Routing, DB DDL)
* **Person 2:** Research & Decision Logic (Triage Spec, Question Bank, Urgency Rubrics)
* **Person 3:** Backend Core & Integration (Question Engine, Priority Engine, Dedup Service, FastAPI Gateway)
* **Person 4:** UI/UX & Frontend (React Cockpit, Interactive Map, Incident Queue)
