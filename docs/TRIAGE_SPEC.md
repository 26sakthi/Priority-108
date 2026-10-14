# PriorityCare Clinical Triage Protocol & Scoring Specification (v1.0)

## 1. Overview
This clinical triage protocol defines the deterministic formulas and decision trees used by the PriorityCare Advisory Copilot in 112/108 emergency operations centers.

## 2. Priority Tiers
* **P1_CRITICAL (Score: 80 - 100):** Immediate threat to life. Requires ALS dispatch with lights and sirens.
  - Fail-Fast trigger: Consciousness = Unresponsive AND/OR Breathing = Absent / Gasping.
  - Target scene response time: < 8 minutes.
* **P2_HIGH_URGENCY (Score: 45 - 79):** Severe illness or acute trauma requiring rapid stabilization.
  - Examples: Uncontrolled moderate bleeding, chest pain with stable vitals, suspected stroke within thrombolysis window.
  - Target scene response time: < 15 minutes.
* **P3_LOWER_URGENCY (Score: 0 - 44):** Stable injury, minor extremity fracture, non-acute illness.
  - Basic BLS / PTS vehicle transport.

## 3. Urgency Scoring Formula
$$\text{UrgencyScore} = \min\left(100, \, B_{\text{category}} + \sum w_i + M_{\text{casualties}} + H_{\text{hazards}}\right)$$

### 3.1 Base Category Urgency ($B_{\text{category}}$)
* `CARDIAC_CHEST_PAIN`: 40
* `RESPIRATORY`: 40
* `ROAD_TRAFFIC_ACCIDENT`: 30
* `UNCONSCIOUS_FALL`: 35
* `STROKE_NEURO`: 35
* `OTHER`: 15

### 3.2 Clinical Symptoms ($w_i$)
* Consciousness:
  - `ALERT`: +0
  - `DROWSY`: +25
  - `UNRESPONSIVE`: +40
* Respiration:
  - `NORMAL`: +0
  - `DIFFICULT`: +35
  - `ABSENT`: +100 (Instant P1 Escalation)
* Hemorrhage:
  - `NONE`: +0
  - `MODERATE`: +15
  - `SEVERE_PUMPING`: +45 (Instant P1 Escalation)
* Trapped Victim (`Q_RTA_TRAPPED == YES`): +25

### 3.3 Multi-Casualty Multiplier ($M_{\text{casualties}}$)
* Casualties $> 1$: $+10$ points.
* Casualties $\ge 5$: $+20$ points (Mass Casualty Incident).

### 3.4 Hazards Addition ($H_{\text{hazards}}$)
* `VEHICLE_FIRE` or `HIGH_VOLTAGE`: $+20$ points.
* `FUEL_LEAK`: $+10$ points.

## 4. Fail-Fast P1 Escalation Rule
If at any moment during the initial 5 questions:
1. `Q_BREATHING == "ABSENT"` OR
2. `Q_BLEEDING == "SEVERE_PUMPING"` OR
3. `Q_CONSCIOUSNESS == "UNRESPONSIVE"` AND `Q_BREATHING == "DIFFICULT"`

The system immediately halts waiting, assigns `priority_tier = "P1_CRITICAL"`, sets `urgency_score = 98`, and generates an instant operator alert banner in $<10$ seconds.
