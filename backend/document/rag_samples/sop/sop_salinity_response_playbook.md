# SOP: Salinity Incident Response Playbook

## 1. Document Control
- Document ID: SOP-SAL-IRR-001
- Version: 1.1
- Status: Approved
- Owner: Operations and Risk Team
- Effective Date: 2026-04-17
- Review Cycle: 12 months
- Language: en
- Scope: irrigation-intake and advisory simulation workflows

## 2. Purpose
Define standardized, auditable response steps for salinity intrusion events in irrigation intake zones, with emphasis on:
- preventing saline water entry into canals and on-farm distribution,
- reducing false alarms from noisy sensor readings,
- preserving traceability for post-incident learning.

## 3. Applicability
- Regions: global template, adaptable by local policy matrix
- Assets: intake gates, pumps, field advisory channels
- Operating mode: simulation-first with human approval controls

## 4.1 Hydro-Operational Context
- Salinity intrusion risk usually increases during low upstream discharge, spring tide phases, and prolonged onshore wind.
- Single-point salinity spikes must be confirmed with trend and contextual checks before escalation.
- Intake decisions should prioritize crop-stage sensitivity and recovery feasibility over short-term convenience.

## 5. Definitions
- Canonical rule unit: dS/m; communication equivalent: g/L (`1 dS/m ~= 0.64 g/L`)
- Warning threshold: salinity >= 2.5 dS/m (~1.60 g/L)
- Critical threshold: salinity >= 4.0 dS/m (~2.56 g/L)
- Fast-rise condition: salinity delta >= 0.3 dS/m (~0.19 g/L) over assessment window
- Safe recovery: salinity remains below warning threshold for at least 3 consecutive checks
- Data freshness: latest valid reading age <= 20 minutes for automatic response pathways
- Sensor confidence check: no hardware fault flag, battery above minimum operating threshold, and timestamp monotonicity preserved

## 6. Responsibilities
- Duty Operator: validates data freshness and initiates first response workflow
- Incident Coordinator: approves escalation messaging and response sequencing
- Reviewer (HITL): approves high-risk plans before execution batch transition
- Data Steward: verifies station metadata integrity and calibration records when quality anomalies appear

## 7. Response Procedure

### 7.1 Detection and Validation (T0 to T+15 min)
1. Confirm latest reading timestamp and sensor station health.
2. Verify at least one prior reading for trend context; if unavailable, mark trend confidence as low.
3. Check trend direction and delta against configured thresholds.
4. Capture tide and wind context snapshot.
5. Cross-check against neighboring station (if available) to detect isolated sensor spikes.
6. Open incident record and attach assessment rationale.

Validation guardrails before escalation:
- Do not escalate solely on one reading if data freshness or sensor confidence fails.
- Require either threshold breach persistence (multiple cycles) or fast-rise + adverse hydro context.

### 7.2 Initial Actions (T+15 to T+30 min)
1. Notify operators and coordinators through dashboard and communication channels.
2. Send farmer advisory for sensitive-crop intake pause in impacted zones.
3. Mark all action proposals as simulation-only until approval checkpoint.
4. Provide explicit next reassessment time in every advisory.

### 7.3 Mitigation Strategy Selection
- Warning level:
  - advisory-first and wait-safe-window simulation preferred
  - avoid abrupt pump start unless local policy explicitly allows
- Critical level:
  - prioritize simulated gate closure and intake pause
  - trigger accelerated human approval path

Recommended strategy modifiers:
- If tide is rising and wind is onshore, prefer conservative closure posture.
- If tide is falling and trend stabilizes, prioritize observation window before restarting intake.
- If crop sensitivity is high (seedling/transplant stage), raise communication urgency.

### 7.4 Approval and Execution Controls
1. High-risk plan execution requires explicit human approval.
2. Record assumptions, constraints, and expected outcome window in decision log.
3. Reject execution if provenance/evidence minimum is not satisfied.
4. Reject execution if salinity unit consistency check fails (dS/m vs g/L mismatch).

### 7.5 Reassessment Cadence
- Critical posture: reassess every 10 to 15 minutes.
- Warning posture: reassess every 20 to 30 minutes.
- Stable recovery: reassess every 30 to 60 minutes until closure criteria are met.

## 8. Recovery and Closure
1. Re-enable normal intake only after safe recovery criteria are met.
2. Use stepwise reopening (partial then full) when local operations support staged control.
3. Continue stakeholder notifications until trend stabilizes.
4. Create post-incident summary and memory-case capture.

Closure minimum evidence:
- three consecutive below-warning readings,
- no fast-rise pattern in latest observation window,
- no active adverse tide/wind trigger requiring continued caution.

## 9. Records and Traceability
- Required records:
  - risk assessment snapshot
  - evidence citations used in planning
  - approval decision and execution summary
  - outcome evaluation and lessons learned

Recommended additional records:
- station health diagnostics during event window
- advisory dissemination timestamps and recipients
- operator overrides with justification

## 10. Metadata
- region_scope: global
- doc_class: sop
- source_standard: IEC-ISO style operational document control
