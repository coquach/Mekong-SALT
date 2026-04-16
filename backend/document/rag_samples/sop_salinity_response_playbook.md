# SOP: Salinity Response Playbook (Mekong-SALT)

## Purpose
Provide consistent operator actions when salinity rises above irrigation-safe conditions.

## Trigger Conditions
- Warning: salinity >= 2.5 dS/m
- Critical: salinity >= 4.0 dS/m
- Fast-rising trend: delta >= 0.3 dS/m over recent window

## Immediate Actions (0-15 minutes)
1. Notify operators and field coordinators.
2. Broadcast advisory to farmers to avoid intake for sensitive crops.
3. Confirm latest sensor timestamp and station health.
4. Check tide and wind context before deciding gate/pump simulation.

## Mitigation Guidance
- At warning level:
  - prefer advisory + wait-safe-window simulation first.
  - avoid abrupt pump start actions.
- At danger/critical levels:
  - prioritize simulated gate closure and intake pause.
  - communicate expected review/approval timeline.

## Human-in-the-loop Requirements
- Any high-risk plan requires explicit human approval before execution.
- Record rationale and assumptions in decision logs.

## Recovery Criteria
- Resume normal intake only when salinity remains below warning threshold across consecutive checks.
- Continue farmer notifications until trend stabilizes.

## Metadata
- region_scope: global
- doc_class: sop
- version: 1.0
