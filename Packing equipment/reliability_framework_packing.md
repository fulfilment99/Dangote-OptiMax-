# Reliability Early-Warning Framework & Risk Scoring Model
## Packing Equipment Predictive Maintenance — DCP University Engineering Challenge, Track 2

---

## 0. Explicit Assumptions

1. **Packing equipment splits into two genuinely different failure physics
   categories**, and this framework treats them differently rather than
   forcing one modeling approach onto both:
   - **Rotating/bearing-driven components** (rotary drive, impeller, palletizer
     servo, conveyor rollers) — these fail the same way any rotating machine
     does (bearing wear), so the CWRU bearing-fault proxy used for kiln and
     mill components is a defensible fit here too.
   - **Wear/calibration components** (spout seals, weighing load cells, bag
     applicator misfeed mechanisms) — these do **not** fail via a
     bearing-vibration signature. Spout seals wear geometrically <cite index="4-1">and are typically replaced once wear reaches 2mm</cite>, tracked by
     physical inspection, not vibration sensors. Weighing drift is a load-cell
     calibration issue — <cite index="4-1">drift of 50-100g between calibrations is described as the largest single source of overfill loss</cite>, but this is
     a metrology problem, not a vibration-detectable fault. No public
     vibration dataset applies to either failure mode, so these are flagged as
     **unmodeled** rather than forced through the bearing classifier.
2. **Severity weights and consequence descriptions are drawn from public
   packing-plant maintenance sources** (cited below), not DCP-confirmed
   figures — treat as a defensible starting point pending real plant input.
3. **Equipment-to-reading assignment remains simulated** for the modeled
   (bearing) components, exactly as in the kiln and mill versions.
4. **The palletizer is flagged as the highest-visibility bottleneck** based on
   the literature, since <cite index="4-1">palletiser and loader failures directly determine dispatch throughput, with deferred service producing the most visible bottlenecks</cite> — this is reflected
   in its severity weight even though it is mechanically less catastrophic
   than a kiln or mill drive failure.

---

## 1. Framework Overview

Same five-stage architecture as kiln and mill:

```
[1] SENSING          [2] FEATURES        [3] CLASSIFICATION      [4] RISK SCORING     [5] ACTION
Rotary drive,     ->  RMS, kurtosis,  ->  CWRU-trained RF     -\                    
impeller, servo,      FFT bands           (bearing components)   >-  Risk Engine  ->  Alert/work
conveyor bearings                                                /   combines           order with
                                                                      P(fault) x         priority tier
Spout seal wear,  ->  No vibration    ->  No model -- flag as    Severity x
weighing drift,       signature           severity-ranked        Detectability
bag misfeeds           applies             only
```

---

## 2. Risk Scoring Formula (unchanged)

```
Risk Score = (P_fault x W_severity x W_detection) x 100
```

---

## 3. Packing Equipment Criticality Table

<cite index="6-1">A roto-packer's core subsystems include the rotating platform, packaging head, weighing system, bag clamp device, feeding system, rotary drive system, dust removal system, and control system</cite>, and <cite index="4-1">a roto packer is described in the literature as eight interlinked subsystems rotating together, where bag accuracy and filling speed depend on every one staying within its wear envelope</cite>.

| Packing Component                          | Failure Consequence                                                        | W_severity | Model Backing |
|----------------------------------------------|--------------------------------------------------------------------------------|:----------:|----------------|
| Rotary drive system (main drive motor bearing) | Stops the entire rotating platform — full packer line stoppage                | 0.80       | Real (CWRU bearing proxy) |
| Impeller / filling head bearing              | <cite index="4-1">Blade erosion drops filling rate and increases dust</cite>, driven by a high-speed motor-bearing assembly | 0.75       | Real (CWRU bearing proxy) |
| Palletizer servo drive / gripper bearing      | <cite index="4-1">Failure modes include gripper wear, pallet stacker alignment, and conveyor tracking</cite>; directly gates dispatch throughput | 0.65       | Real (CWRU bearing proxy) |
| Weighing system / load cell (metrology drift) | <cite index="4-1">Drift of 50-100g between calibrations is the largest single source of overfill loss</cite> — an economic/compliance risk, not a stoppage risk | 0.55       | None — flagged (calibration issue, not vibration-detectable) |
| Spout seal / cone wear                        | <cite index="4-1">Worn cones leak product and disrupt weight accuracy</cite>, replaced on a physical wear-depth schedule | 0.45       | None — flagged (geometric wear, not vibration-detectable) |
| Conveyor belt / roller bearing                 | Belt tracking and roller bearing wear cause line stoppages, generally recoverable quickly | 0.35       | Real (CWRU bearing proxy) |
| Bag applicator misfeed mechanism               | <cite index="4-1">A bag applicator running below its design accuracy rate can stop the line dozens of times per shift for misfeeds</cite> — frequent but low-severity per event | 0.30       | None — flagged (pneumatic/mechanical actuation fault, not bearing vibration) |

---

## 4. Detection Confidence Weight (unchanged)

```
margin = P(predicted class) - P(second most likely class)
W_detection = 0.5 + 0.5 x margin
```

---

## 5. Risk Tiers and Recommended Actions (unchanged)

| Risk Score | Tier         | Recommended Action                                                    |
|:----------:|--------------|----------------------------------------------------------------------------|
| 80 - 100   | **Critical** | Immediate inspection; plan controlled stop                                  |
| 55 - 79    | **High**     | Schedule inspection within 1-2 weeks; increase monitoring frequency          |
| 30 - 54    | **Medium**   | Add to next planned maintenance window; monitor trend                        |
| 0 - 29     | **Low**      | No action; continue routine monitoring                                       |

For the three unmodeled components, report a **fixed inspection interval
recommendation** instead of a live risk score — e.g. spout seal wear-depth
checks and load-cell calibration on a running-hours schedule, which is
consistent with how <cite index="1-1">packing plant maintenance is described in the literature as covering scheduled servicing of rotary packers, impeller assemblies, spout seals, filling heads, and air systems on running-hours intervals rather than failure triggers</cite>.

---

## 6. Why This Framework Matters

- It correctly separates **rotating-machinery faults** (which your ML model
  can genuinely detect) from **wear/calibration faults** (which fundamentally
  need a different sensing approach — ultrasonic thickness gauging for seals,
  scheduled calibration for load cells). Presenting this distinction honestly
  is stronger than forcing every component through one classifier.
- It reuses the exact same scoring architecture and even the same trained
  CWRU model as the kiln and mill frameworks — reinforcing the "one
  reliability engine, three equipment classes" architectural story for your
  submission.
- It ties severity weighting to a real operational consequence — dispatch
  throughput and legal metrology compliance — rather than only mechanical
  catastrophe, since packing equipment failures show up as revenue loss and
  compliance risk more than kiln-style stoppage risk.
