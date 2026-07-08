# Reliability Early-Warning Framework & Risk Scoring Model
## Cement / Raw Mill Predictive Maintenance — DCP University Engineering Challenge, Track 2

---

## 0. Explicit Assumptions

State these plainly in your submission — they are what a judge will probe first,
and naming them yourself is more credible than hoping they go unnoticed.

1. **Equipment scope.** This framework is built around a **ball mill** (the
   dominant grinding technology for cement finish milling and common in many
   Nigerian plants), with notes on where a **Vertical Roller Mill (VRM)**
   differs. We did not confirm which mill type(s) DCP operates at the plant(s)
   this submission targets — this should be verified before final submission
   if that information becomes available.
2. **Severity weights are literature-derived estimates, not DCP-confirmed
   figures.** They are informed by published industry sources on cement mill
   failure consequence and typical downtime (cited in Section 3), not DCP's
   actual maintenance records or cost data, which your team does not have
   access to. Treat them as a defensible starting point, not ground truth.
3. **Proxy sensor data.** As with the kiln model, no real DCP mill sensor data
   is available to this team. The classifier was trained on the CWRU bearing
   dataset (real, externally recorded vibration data — see prior methodology
   note) as a proxy for mill trunnion and gearbox bearing signals. The physics
   of rolling-element bearing failure is the same regardless of which machine
   the bearing sits in, which is why this proxy is defensible — but the
   absolute probability values would shift once retrained on real mill data.
4. **Equipment-to-reading assignment is simulated**, exactly as in the kiln
   model — in a real deployment, each sensor reading is tied to a known
   physical sensor location, not randomly assigned.
5. **Downtime cost figures cited below are industry-wide ranges from public
   sources, not DCP-specific figures.** Use them only to justify relative
   severity ordering (which component matters more), not as precise financial
   claims in your business case unless DCP shares real figures.

---

## 1. Framework Overview

Identical five-stage structure to the kiln framework, applied to mill sensors:

```
[1] SENSING     [2] FEATURES     [3] CLASSIFICATION   [4] RISK SCORING     [5] ACTION
Vibration/temp  ->  RMS, kurtosis, ->  ML model predicts ->  Risk Engine   ->  Alert/work
on trunnion,        FFT bands          fault presence/       combines           order with
gearbox, motor,     per window         type + confidence     P(fault) x         priority tier
liner sensors                                                Severity x
                                                               Detectability
```

The same trained classifier (Random Forest, ~97% multiclass accuracy on the
proxy dataset) is reused here — a genuine strength of this framework is that
**the classification and scoring architecture is equipment-agnostic**; only
the severity table and sensor placement change between kiln and mill.

---

## 2. Risk Scoring Formula (unchanged)

```
Risk Score = (P_fault x W_severity x W_detection) x 100
```

Same definitions as the kiln model:
- **P_fault** — model's predicted probability of a fault, from `predict_proba`
- **W_severity** — consequence weight for this mill component (Section 3)
- **W_detection** — `0.5 + 0.5 x margin`, where margin is the gap between the
  model's top-two predicted class probabilities (penalizes low-confidence,
  borderline predictions)

---

## 3. Mill Equipment Criticality Table (Severity Weights)

| Mill Component                          | Failure Consequence                                                              | W_severity | Basis |
|-------------------------------------------|-------------------------------------------------------------------------------------|:----------:|-------|
| Trunnion bearing (ball mill)               | Catastrophic — supports full mill weight (hundreds of tonnes); seizure risks shell damage <cite index="7-1,7-2">Trunnion bearings support the entire mill weight, and lubrication starvation, contamination, or misalignment leads to overheating, seizure, and potential shell damage.</cite> | 1.00 |
| Girth gear / pinion / gearbox              | Catastrophic — transmits massive torque; gearbox failures can extend downtime by <cite index="2-1">12–16 weeks while replacement gearboxes are sourced</cite> | 0.95 |
| Grinding table / rollers (VRM only)        | Severe — <cite index="4-1">roller and table liner wear is predicted from vibration and power signatures</cite>; hydraulic system pressure is a leading indicator | 0.80 |
| Mill shell liners                          | Moderate-severe — worn liners reduce grinding efficiency and risk shell damage if bolts fail loose | 0.55 |
| Main drive motor bearings                  | Moderate — <cite index="3-1">among the 32–44 critical monitoring points on a typical ball mill</cite>, but generally more replaceable than trunnion/gearbox | 0.50 |
| Separator bearings                         | Lower — affects product fineness/classification efficiency, not structural integrity | 0.30 |
| Mill fan / auxiliary bearings              | Lower — <cite index="5-1">cooling and process fans are monitored for imbalance and bearing wear via vibration and motor current signature analysis</cite>, but usually has redundancy | 0.25 |

Two supporting figures worth citing in your Concept Note's business case:
<cite index="6-1">bearing and coupling faults in a cement mill gearbox can halt production for up to 3 days, while structural looseness and misalignment in mill components can cause close to 30 hours of downtime</cite>. Separately, <cite index="7-1">roughly 80% of ball mill bearing failures are lubrication-related rather than fatigue-related</cite> — worth noting since it suggests oil analysis integration (not just vibration) meaningfully improves detection lead time, a point you can raise as a "Phase 2" extension.

---

## 4. Detection Confidence Weight (unchanged formula, same rationale)

```
margin = P(predicted class) - P(second most likely class)
W_detection = 0.5 + 0.5 x margin
```

---

## 5. Risk Tiers and Recommended Actions

| Risk Score | Tier         | Recommended Action                                                  |
|:----------:|--------------|------------------------------------------------------------------------|
| 80 - 100   | **Critical** | Immediate inspection; plan controlled stop — trunnion/gearbox faults justify stopping the mill before a bearing seizure damages the shell |
| 55 - 79    | **High**     | Schedule inspection within 1-2 weeks; add oil analysis sample given lubrication is the dominant failure driver |
| 30 - 54    | **Medium**   | Add to next planned maintenance window; monitor vibration trend         |
| 0 - 29     | **Low**      | No action; continue routine monitoring                                  |

Tier boundaries carried over unchanged from the kiln model for consistency
across your submission — recalibrate against real mill maintenance lead times
(gearbox procurement in particular runs far longer than most parts, per
Section 3) once real data is available.

---

## 6. Kiln vs. Mill: What Changes, What Doesn't

| Element                     | Kiln Model                                | Mill Model                                  |
|------------------------------|--------------------------------------------|----------------------------------------------|
| Classifier                  | Same Random Forest architecture             | Same Random Forest architecture               |
| Feature extraction pipeline | Identical (RMS, kurtosis, FFT bands)        | Identical                                     |
| Severity table               | Kiln-specific (drive, rollers, tyre, shell) | Mill-specific (trunnion, gearbox, liners)      |
| Risk formula                 | Identical                                   | Identical                                      |
| Highest-severity component   | Main Drive Motor / Girth Gear (1.00)        | Trunnion Bearing (1.00)                        |

This reuse is worth stating explicitly to judges: **the same underlying
reliability engine scales across equipment types** by swapping only the
severity table — this is a meaningful signal of architectural soundness for
a plant-wide (not single-machine) deployment, which is what DCP would actually need.
