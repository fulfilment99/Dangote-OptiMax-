# Reliability Early-Warning Framework & Risk Scoring Model
## Coal Mill Predictive Maintenance — DCP University Engineering Challenge, Track 2

---

## 0. Explicit Assumptions

1. **Coal mill type assumed: applies to both vertical roller mill (VRM) and
   air-swept ball mill**, since <cite index="31-1">the most common types of coal mills in cement manufacturing are vertical roller mills and air-swept ball mills</cite> — both share the same mechanical/gearbox
   components this framework models. Which type DCP operates was not
   confirmed.
2. **Fire and explosion risk is deliberately kept OUT of the 0-100 risk
   scoring model and treated as a separate, parallel safety system.** This is
   the most important judgment call in this document. Coal mills carry a
   hazard that kiln, cement mill, packing, and crusher equipment do not:
   <cite index="28-1">spontaneous combustion in pile cores starts at 80°C, with ignition possible from 800°C coal surface temperature, tramp iron sparks, or bearing failures</cite>, and <cite index="28-1">the cement industry predominantly uses indirect firing systems operating at intentionally low oxygen atmospheres, often 3-8% O2</cite>, where an oxygen excursion is what turns a fire hazard into an explosion hazard.
   Blending an explosion-risk indicator into the same ranked list as "packing
   line bearing wear" would risk a Critical-tier bearing alert visually
   outranking a smaller but genuinely dangerous gas-threshold breach. Section
   6 below defines this as a separate, always-on safety layer, not a
   component competing for attention in the reliability risk matrix.
3. **Bearing-driven mechanical components** (main/roller bearing, girth
   gear/gearbox, rotary feeder, seal air fan, classifier drive) follow the
   same "real proxy dataset" approach as prior frameworks — CWRU for bearings,
   the SpectraQuest gearbox dataset for the gearbox.
4. **Grinding table/roller wear (VRM) and mill liners remain unmodeled**,
   consistent with the cement mill framework — no public vibration dataset
   applies to geometric wear tracked by thickness measurement.
5. **Severity weights are literature-derived estimates** from industry
   sources cited below, not DCP-confirmed figures.
6. **Equipment-to-reading assignment remains simulated** for modeled
   components, consistent with all prior framework versions.

---

## 1. Framework Overview

```
[1] SENSING           [2] FEATURES        [3] CLASSIFICATION      [4] RISK SCORING     [5] ACTION
Bearing vibration  ->  RMS, kurtosis,  ->  CWRU-trained RF     -\                    
(main/roller/feeder/    FFT bands           (bearing components)   >-  Risk Engine  ->  Alert/work
fan/classifier)                                                    /   (0-100 score)      order with
Gearbox vibration  ->  Same pipeline   ->  Gearbox-trained RF -/    combines P(fault)     priority tier
                                                                     x Severity x
Grinding table/     ->  No sensor data available -> severity-only flag  Detectability
liner wear

--- SEPARATE SAFETY LAYER (not blended into the 0-100 score above) ---
CO concentration,   ->  Threshold-based alarm logic -> dedicated safety alert,
O2 level, mill           (not ML classification)         independent of
outlet temperature                                        maintenance risk tier
```

---

## 2. Risk Scoring Formula (mechanical components only, unchanged)

```
Risk Score = (P_fault x W_severity x W_detection) x 100
```

---

## 3. Coal Mill Equipment Criticality Table (Mechanical/Reliability Scope)

<cite index="31-1">Components such as the rotary feeder, classifier, and seal air fans are prone to wear-tear and mechanical faults which could disrupt the coal mill's functioning</cite>, and <cite index="31-1">bearing and gearbox defects in the mill can result in as much as 56 hours of unplanned production downtime</cite>.

| Coal Mill Component                       | Failure Consequence                                                         | W_severity | Model Backing |
|----------------------------------------------|-------------------------------------------------------------------------------|:----------:|----------------|
| Main / grinding roller bearing                | Same catastrophic-stoppage class as other mill types; halts coal supply to kiln burner | 1.00       | Real (CWRU bearing proxy) |
| Girth gear / pinion / gearbox                  | <cite index="25-1">Bearing and coupling faults in mill gearboxes can halt production for up to 3 days</cite> | 0.95       | Real (Gearbox dataset — direct match) |
| Grinding table / rollers (VRM)                 | <cite index="27-1">Grinding roller wear creates characteristic vibration signatures and motor current increases as the rolling surface degrades</cite>, but tracked via wear-depth survey, not classified by this model | 0.80       | None — flagged |
| Classifier / separator drive bearing            | Governs coal powder fineness; failure disrupts combustion quality at the burner | 0.55       | Real (CWRU bearing proxy) |
| Mill liners                                     | Wear part; same physics as cement mill liners | 0.55       | None — flagged |
| Rotary feeder bearing                           | <cite index="31-1">Prone to wear-tear and mechanical faults which could disrupt the coal mill's functioning</cite> | 0.45       | Real (CWRU bearing proxy) |
| Seal air fan bearing                            | <cite index="31-1">Prone to wear-tear and mechanical faults</cite>; generally has redundancy | 0.35       | Real (CWRU bearing proxy) |

---

## 4. Detection Confidence Weight (unchanged)

```
margin = P(predicted class) - P(second most likely class)
W_detection = 0.5 + 0.5 x margin
```

---

## 5. Risk Tiers and Recommended Actions (mechanical scope, unchanged)

| Risk Score | Tier         | Recommended Action                                                    |
|:----------:|--------------|------------------------------------------------------------------------|
| 80 - 100   | **Critical** | Immediate inspection; plan controlled stop                              |
| 55 - 79    | **High**     | Schedule inspection within 1-2 weeks; increase monitoring frequency      |
| 30 - 54    | **Medium**   | Add to next planned maintenance window; monitor trend                    |
| 0 - 29     | **Low**      | No action; continue routine monitoring                                   |

---

## 6. Fire & Explosion Safety Layer (separate from the reliability model)

This is deliberately **not** a "Critical" tier in the same table above. It is
a distinct, always-on threshold-alarm system, because the response required
is different in kind (emergency shutdown/inertisation procedure) from a
maintenance work order.

| Signal                        | Threshold / Behavior                                                          | Response |
|--------------------------------|----------------------------------------------------------------------------------|----------|
| Mill outlet temperature         | <cite index="28-1">Smouldering risk becomes active above 90°C at the mill outlet; inlet air is generally capped at 400°C</cite> | Immediate operator alert; trend monitored continuously |
| Pile/deposit temperature        | <cite index="28-1">Spontaneous combustion in pile cores starts at 80°C</cite> | Immediate inspection of dead zones / deposits |
| O2 concentration (indirect firing) | <cite index="28-1">Normal operation is 3-8% O2 from preheater tail gas; excursions above the limiting oxygen concentration turn a fire hazard into an explosion hazard</cite> | Automatic trip / inertisation per plant safety system, not an ML prediction |
| CO concentration                 | <cite index="28-1">CO analysers are installed on virtually every cement coal grinding system</cite> as the primary early-combustion indicator | Escalating alarm bands feeding directly into a forced-shutdown permit workflow |

**Why this is out of scope for the ML classifier in this submission:** these
are threshold/rate-of-change safety interlocks governed by established plant
safety systems (gas analysers, temperature probes wired to trip logic), not
a pattern-classification problem suited to the vibration-based approach used
elsewhere in this challenge. Presenting a "risk score" for explosion risk
from a bearing-vibration-trained model would overstate what that model can
responsibly claim to do. If your team wants to extend into this area, frame
it as a **future integration point** (ingesting CO/O2/temperature sensor
feeds into the same dashboard, with its own independent alarm logic) rather
than folding it into the Section 2 formula.

---

## 7. Why This Framework Matters

- Completes a **five-equipment-class reliability engine** (kiln, cement mill,
  packing, crusher, coal mill) on one consistent scoring method.
- Demonstrates judgment, not just modeling — recognizing that one component
  category (fire/explosion) genuinely does not belong in the same scoring
  system as the others is a stronger engineering position than force-fitting
  everything through the same pipeline for consistency's sake.
