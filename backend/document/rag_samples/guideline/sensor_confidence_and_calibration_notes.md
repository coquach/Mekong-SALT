# Guideline: Sensor Confidence and Calibration Notes

## 1. Document Control
- Document ID: GL-SENSOR-QUAL-003
- Version: 1.0
- Status: Approved
- Effective Date: 2026-04-17
- Language: en

## 2. Objective
Provide a reference checklist for judging whether a salinity reading is trustworthy enough to drive escalation or remain in observation mode.

## 3. Confidence Checks
- Timestamp monotonicity: readings must not move backward for the same station unless explicitly annotated as backfill.
- Freshness: prefer readings observed within the current reassessment window.
- Battery and diagnostics: low battery or hardware fault flags reduce confidence.
- Neighbour comparison: if a neighboring station is stable and one point spikes, treat the spike as suspect until confirmed.
- Trend continuity: a single spike without follow-up confirmation should not override the broader trend.

## 4. Calibration and Maintenance Notes
- Use the configured calibration cycle for each station metadata record.
- If the station has recently been serviced, annotate the event in metadata so operators can interpret short-term anomalies.
- Missing calibration evidence does not invalidate every reading, but it should increase the review requirement for escalation.

## 5. Operational Guidance
- If confidence is low, the system should keep observation posture instead of immediate gate action.
- If confidence is medium and salinity is rising, increase reassessment frequency.
- If confidence is high and the salinity band is danger or critical, proceed to plan drafting and approval.

## 6. Metadata
- region_scope: global
- doc_class: guideline
- source_standard: internal reference guidance