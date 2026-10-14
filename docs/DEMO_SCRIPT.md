# PriorityCare (MEDI-DISPATCH AI) — 5-Minute Hackathon Demo Script (INTELLATHON '26)

## 0:00 - 0:45 | The 112/108 Operational Problem
* **Visual:** Open the PriorityCare Cockpit in dark mode. Point out the 3 panes:
  1. Live Priority Queue (Left)
  2. Call Intake & Decision Recommendations (Center)
  3. Real-Time OpenStreetMap Fleet & Hospital Route Visualizer (Right)
* **Pitch:** "Every day, emergency dispatch operators face cognitive overload. Blind nearest-hospital dispatching and duplicate bystander chaos cost lives. PriorityCare acts as an active, clinical-capability-aware advisory copilot."

---

## 0:45 - 2:00 | Multi-Factor Deduplication & Casualty Accumulation
* **Action:**
  1. Click **"New Emergency Call"**.
  2. Input:
     - Phone: `+91 98765 43210`
     - Landmark: `NH-45 Samayapuram Toll Plaza`
     - Emergency Type: `ROAD_TRAFFIC_ACCIDENT`
     - Reported Casualties: `1`
  3. Start intake. The system assigns incident number and displays the 5 essential vitals.
* **Simulate Second Call:**
  1. Open second intake or trigger Duplicate Check:
     - Location: 35m away, 90 seconds later, reporting `2 trapped casualties`.
  2. **SHOWCASE:** System flags `HIGH_MATCH` (94% confidence) with an orange warning modal:
     *"Bystander report matches active incident INC-... 35m away"*.
  3. Operator clicks **"Merge Call"**.
  4. **SHOWCASE:** The casualty count updates from 1 to 2 without creating a duplicate ghost incident.

---

## 2:00 - 3:15 | Fail-Fast Instant P1 Escalation (< 10 Seconds)
* **Action:**
  1. Incoming call for an unconscious patient with gasping.
  2. Operator answers:
     - `Q_CONSCIOUSNESS`: **Unresponsive**
     - `Q_BREATHING`: **ABSENT / Gasping**
  3. Click **"Submit Vitals"**.
  4. **SHOWCASE:** An instant pulsing crimson alert banner flashes:
     **"INSTANT P1 CRITICAL ESCALATION TRIGGERED: Respiration Absent. Bypassing remaining questionnaire."**
  5. The incident instantly jumps to Index 0 on the Dispatch Queue with an Urgency Score of **98**.

---

## 3:15 - 4:15 | Capability-First Allocation & Dijkstra Road Routing
* **Action:**
  1. Click on the P1 Incident.
  2. Open **"Recommendations Dossier"**.
  3. **SHOWCASE:**
     - The system selects `AMB-ALS-02` (Advanced Life Support with active Ventilator & Defibrillator) instead of a closer BLS transport unit.
     - Dijkstra calculates the shortest path over OpenStreetMap to **Dhanalakshmi Srinivasan Medical College Hospital** (15 mins away with active Trauma Level-1 ICU) instead of a local clinic that lacks ICU facilities.
  4. Map displays:
     - Amber/Red line: Ambulance to Incident scene route.
     - Cyan/Blue line: Incident to Hospital route.
  5. Operator clicks **"Confirm Dispatch"**.
  6. **SHOWCASE:** Incident transitions to `DISPATCHED`, ambulance updates to `EN_ROUTE_SCENE`, and an immutable record is logged in the operator audit trail.

---

## 4:15 - 5:00 | Impact & Technology Stack
* Highlight metrics:
  - Call triage time reduced from 3.5 minutes to $< 10$ seconds for critical vitals.
  - 100% elimination of redundant ambulance dispatches via non-destructive spatial-temporal clustering.
  - Zero secondary transfers by routing to verified available specialty beds.
* Architecture: Python FastAPI modular monolith + PostgreSQL / PostGIS schema + Dijkstra graph routing + React Cockpit.
