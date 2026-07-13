# Reliability Early-Warning Framework & Risk Scoring Model (v2)
## Cement Mill Predictive Maintenance — DCP University Engineering Challenge, Track 2
### Now integrating two real, fault-specific proxy datasets

---

## 0. Explicit Assumptions

1. **Two separate real datasets now back this model, not one.**
   - **CWRU Bearing Dataset** (Case Western Reserve University) — real vibration
     data from bearings with seeded ball/inner-race/outer-race defects — used
     for all **bearing** components (trunnion, motor, fan, separator).
   - **Gearbox Fault Diagnosis Dataset** (GitHub: Gearboxdata) — real vibration
     data from a healthy vs. broken-tooth gearbox across 10 load conditions —
     used for the **girth gear / pinion / gearbox** component specifically.
   Neither dataset is DCP's own sensor data; both are real, externally
   recorded, physical experiments used as proxies until real plant data is
   available.

2. **Two mill components have no matching public dataset and are explicitly
   unmodeled** — the risk score for these is not backed by a trained
   classifier's prediction, only by the severity weight itself:
   - **Mill shell liners** — liner wear is typically assessed via ultrasonic
     thickness gauging or manual inspection, not vibration, so it doesn't fit
     either proxy dataset's sensing modality.
   - **Grinding table / rollers (VRM only)** — no public vibration dataset
     specific to VRM table/roller wear was found; this framework flags it as a
     "monitor via severity only" component until either real data or a closer
     proxy is available. Do not present a P_fault number for this component
     as if it came from a trained model — none does.

3. **Gearbox dataset sample rate is assumed, not confirmed** (see
   `extract_gearbox_features.py` for the specific caveat) — frequency-domain
   features from that model are internally consistent for classification but
   not calibrated to real physical frequencies.

4. **Equipment-to-reading assignment remains simulated** for the components
   that do have a trained model (trunnion, motor, fan, separator, gearbox) —
   in deployment, each reading is tied to a known physical sensor, not
   randomly assigned as done here for demonstration.

5. **Severity weights are literature-derived estimates**, cited to public
   industry sources (Section 3), not DCP-confirmed figures.

---

## 1. Framework Overview

```
[1] SENSING          [2] FEATURES        [3] CLASSIFICATION        [4] RISK SCORING      [5] ACTION
Bearing vibration ->  RMS, kurtosis,  ->  CWRU-trained RF        -\                    
(trunnion/motor/       FFT bands           (bearing components)    >-  Risk Engine  ->  Alert/work
 fan/separator)                                                    /   combines           order with
Gearbox vibration ->  Same feature    ->  Gearbox-trained RF    -/    P(fault) x          priority tier
(girth gear)           pipeline            (gearbox component)       Severity x
                                                                      Detectability
Liner / VRM table  ->  No sensor data available -> severity-only flag, no model prediction
```

---

## 2. Risk Scoring Formula (unchanged)

```
Risk Score = (P_fault x W_severity x W_detection) x 100
```

The only change from v1: **P_fault now comes from two different trained
models depending on which component the reading belongs to**, rather than a
single model's output reused everywhere.

| Component                          | P_fault source                          |
|-------------------------------------|--------------------------------------------|
| Trunnion Bearing (Ball Mill)         | CWRU-trained Random Forest                  |
| Main Drive Motor Bearing             | CWRU-trained Random Forest                  |
| Mill Fan / Auxiliary Bearing         | CWRU-trained Random Forest                  |
| Separator Bearing                    | CWRU-trained Random Forest                  |
| Girth Gear / Pinion / Gearbox        | Gearbox-trained Random Forest (real gear-fault data) |
| Mill Shell Liners                    | No model — severity-weight-only flag        |
| Grinding Table / Rollers (VRM)       | No model — severity-weight-only flag        |

---

## 3. Mill Equipment Criticality Table (Severity Weights — unchanged from v1)

| Mill Component                     | W_severity | Model Backing |
|--------------------------------------|:----------:|----------------|
| Trunnion bearing (ball mill)          | 1.00       | Real (CWRU proxy) |
| Girth gear / pinion / gearbox         | 0.95       | Real (Gearbox dataset — direct match) |
| Grinding table / rollers (VRM only)    | 0.80       | None — flagged |
| Mill shell liners                     | 0.55       | None — flagged |
| Main drive motor bearings              | 0.50       | Real (CWRU proxy) |
| Separator bearings                     | 0.30       | Real (CWRU proxy) |
| Mill fan / auxiliary bearings          | 0.25       | Real (CWRU proxy) |

---

## 4. Detection Confidence Weight (unchanged)

```
margin = P(predicted class) - P(second most likely class)
W_detection = 0.5 + 0.5 x margin
```

Computed independently per model — the CWRU model's margin for bearing
readings, the gearbox model's margin for gearbox readings.

---

## 5. Risk Tiers and Recommended Actions (unchanged)

| Risk Score | Tier         | Recommended Action                                             |
|:----------:|--------------|------------------------------------------------------------------|
| 80 - 100   | **Critical** | Immediate inspection; plan controlled stop                        |
| 55 - 79    | **High**     | Schedule inspection within 1-2 weeks; add oil analysis if bearing-related |
| 30 - 54    | **Medium**   | Add to next planned maintenance window; monitor trend              |
| 0 - 29     | **Low**      | No action; continue routine monitoring                             |

For **liner** and **VRM table/roller** components (no trained model), report
these separately in your submission as "severity-ranked, not yet ML-scored" —
this is more credible than assigning them a fabricated P_fault.

---

## 6. Why This Version Is Stronger

- **Fault-specific data per failure mode**, not one generic proxy reused
  everywhere — gearbox faults are modeled on real gear data, bearing faults
  on real bearing data.
- **Honest about coverage gaps** — two components are explicitly unmodeled
  rather than silently faked, which is a stronger position with judges than
  quietly filling every cell with a number.
- **Same scoring architecture as the kiln model** — proving the engine
  generalizes across equipment types and across which underlying classifier
  feeds it, which is the real architectural claim worth making to DCP.
