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
Define standardized, auditable response steps for salinity events in irrigation intake zones.

## 3. Applicability
- Regions: global template, adaptable by local policy matrix
- Assets: intake gates, pumps, field advisory channels
- Operating mode: simulation-first with human approval controls

## 4. Definitions
- Canonical rule unit: dS/m; communication equivalent: g/L (`1 dS/m ~= 0.64 g/L`)
- Warning threshold: salinity >= 2.5 dS/m (~1.60 g/L)
- Critical threshold: salinity >= 4.0 dS/m (~2.56 g/L)
- Fast-rise condition: salinity delta >= 0.3 dS/m (~0.19 g/L) over assessment window
- Safe recovery: salinity remains below warning threshold for at least 3 consecutive checks

## 5. Responsibilities
- Duty Operator: validates data freshness and initiates first response workflow
- Incident Coordinator: approves escalation messaging and response sequencing
- Reviewer (HITL): approves high-risk plans before execution batch transition

## 6. Response Procedure

### 6.1 Detection and Validation (T0 to T+15 min)
1. Confirm latest reading timestamp and sensor station health.
2. Verify trend direction and delta against configured thresholds.
3. Capture tide and wind context snapshot.
4. Open incident record and attach assessment rationale.

### 6.2 Initial Actions (T+15 to T+30 min)
1. Notify operators and coordinators through dashboard and communication channels.
2. Send farmer advisory for sensitive-crop intake pause in impacted zones.
3. Mark all action proposals as simulation-only until approval checkpoint.

### 6.3 Mitigation Strategy Selection
- Warning level:
  - advisory-first and wait-safe-window simulation preferred
  - avoid abrupt pump start unless local policy explicitly allows
- Critical level:
  - prioritize simulated gate closure and intake pause
  - trigger accelerated human approval path

### 6.4 Approval and Execution Controls
1. High-risk plan execution requires explicit human approval.
2. Record assumptions, constraints, and expected outcome window in decision log.
3. Reject execution if provenance/evidence minimum is not satisfied.

## 7. Recovery and Closure
1. Re-enable normal intake only after safe recovery criteria are met.
2. Continue stakeholder notifications until trend stabilizes.
3. Create post-incident summary and memory-case capture.

## 8. Records and Traceability
- Required records:
  - risk assessment snapshot
  - evidence citations used in planning
  - approval decision and execution summary
  - outcome evaluation and lessons learned

## 9. Metadata
- region_scope: global
- doc_class: sop
- source_standard: IEC-ISO style operational document control
