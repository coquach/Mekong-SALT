# Guideline: Weather and Tide Operational Decision Support

## 1. Document Control
- Document ID: GL-WTH-TIDE-002
- Version: 1.1
- Status: Approved
- Effective Date: 2026-04-17
- Language: en

## 2. Objective
Provide standardized environmental interpretation rules for salinity response planning.

## 3. Hydrometeorological Signals to Monitor
- Tide phase and amplitude (rising, high slack, falling).
- Wind direction and speed relative to estuary axis (onshore vs offshore tendency).
- Upstream freshwater support proxy (if available from basin operations).
- Rainfall recency and duration (short pulses may dilute locally but not persist).

## 4. Operational Heuristics
- Onshore wind + rising tide generally increase saline intrusion pressure near intake points.
- If tide is near peak and salinity trend is rising, prioritize simulated gate closure over pump start.
- During falling tide with stable-to-falling salinity trend, wait-safe-window may be preferred before intake restart.
- A one-cycle salinity dip during strong onshore wind should not be treated as definitive recovery.
- Strong rainfall shortly after peak salinity may produce temporary improvement; confirm persistence before reopening.

## 5. Decision Support Matrix (Interpretation)
- Tide rising + trend rising: high caution posture, shorten reassessment interval.
- Tide high slack + trend stable at elevated level: maintain protection posture, avoid premature reopening.
- Tide falling + trend falling: candidate recovery window, apply staged verification checks.
- Tide rising + trend falling: mixed signal, require extra confirmation cycle before changes.

## 6. Communication Requirements
- Every advisory should include reassessment interval and expected next update time.
- Every outbound notification must state whether actions are simulation-only.

Template advisory fields:
- current salinity and trend
- tide phase and weather modifiers
- current posture (monitor / caution / protection)
- next review timestamp

## 7. Risk Framing Guidance
- Warning scenarios: advisory + observation-first actions are often sufficient.
- Critical scenarios: combine communication with hydraulic mitigation simulation and mandatory HITL review.

## 8. Known Limits and Failure Modes
- Local station anomalies can mimic hydro events; always check sensor confidence.
- Tide forecasts and observed tide may diverge in complex channels.
- Regional heterogeneity means one station should not represent all intake points.

## 9. Assumptions and Limits
- This guideline complements, not overrides, local threshold policy matrix.
- Final execution is constrained by approval policy and safety controls.

## 10. Metadata
- region_scope: global
- doc_class: guideline
- source_standard: operational decision support note
