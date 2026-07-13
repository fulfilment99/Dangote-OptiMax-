# Reliability Early-Warning Framework & Risk Scoring Model
## Crusher Predictive Maintenance — DCP University Engineering Challenge, Track 2

---

## 0. Explicit Assumptions

1. **Crusher type assumed: jaw crusher as primary reference**, since it is the
   most common primary crusher in cement raw-material circuits, with notes on
   impact/hammer crusher rotor components where they differ. Which specific
   crusher type(s) DCP operates was not confirmed — verify before final
   submission if that information becomes available.
2. **This framework has a stronger evidentiary basis than the mill and
   packing versions on one point**: the severity ordering below is partly
   supported by a peer-reviewed source, not only vendor content. A published
   study on jaw crusher reliability in a cement plant found that <cite index="20-1">wear-related failures such as jaw plate wear and bearing failures constitute more than 60% of breakdowns, while lubrication problems contribute to 25% of failures</cite> — this is an academic MTBF/MTTR study, not a maintenance-software vendor's blog, and is cited separately from the vendor sources below for that reason.
3. **As with mills and packing, this splits into two failure-physics
   categories**:
   - **Bearing-driven components** (eccentric shaft, drive motor, rotor
     housing, countershaft) — CWRU bearing-fault proxy is a defensible fit.
   - **Wear/structural components** (jaw plate/blow bar, toggle plate, CSS
     setting mechanism) — these fail via material wear or fatigue cracking,
     tracked by thickness survey or visual inspection, not vibration
     signature. No public vibration dataset applies; flagged as unmodeled.
4. **Severity weights** are a mix of the peer-reviewed source above and
   industry vendor content (cited individually below) — treat as a
   defensible estimate, not DCP-confirmed figures.
5. **Equipment-to-reading assignment remains simulated** for modeled
   components, consistent with all prior framework versions.

---

## 1. Framework Overview

```
[1] SENSING          [2] FEATURES        [3] CLASSIFICATION      [4] RISK SCORING     [5] ACTION
Eccentric shaft,  ->  RMS, kurtosis,  ->  CWRU-trained RF     -\                    
motor, rotor,          FFT bands           (bearing components)   >-  Risk Engine  ->  Alert/work
countershaft                                                     /   combines           order with
bearings                                                             P(fault) x         priority tier
                                                                      Severity x
Jaw plate/blow    ->  No vibration    ->  No model -- flag as    Detectability
bar wear, toggle       signature           severity-ranked
plate, CSS drift       applies             only (thickness/
                                            visual inspection)
```

---

## 2. Risk Scoring Formula (unchanged)

```
Risk Score = (P_fault x W_severity x W_detection) x 100
```

---

## 3. Crusher Equipment Criticality Table

<cite index="19-1">Cement plant crushers process 800-3,000 tonnes of limestone per hour, enduring continuous impact forces that wear jaw plates, toggle assemblies, and bearings at predictable rates</cite>, and <cite index="19-1">when a primary crusher fails without warning, the raw mill starves within hours and the kiln feed runs dry within a shift</cite> — making the crusher's severity weights structurally tied to the entire downstream process, not just local damage.

| Crusher Component                          | Failure Consequence                                                             | W_severity | Model Backing |
|-----------------------------------------------|---------------------------------------------------------------------------------|:----------:|----------------|
| Eccentric / main shaft bearing                | <cite index="21-1">Deterioration here is one of the primary signals tracked, with a 3-6 week detection window before failure</cite>; drives the entire crushing motion | 1.00       | Real (CWRU bearing proxy) |
| Rotor bearing housing (impact/hammer crusher)  | <cite index="23-1">Rotor imbalance and bearing fatigue cause vibration-induced structural cracking and unplanned stoppages that disrupt raw material supply to the mill</cite> | 0.80       | Real (CWRU bearing proxy) |
| Jaw plate / blow bar / hammer wear             | <cite index="20-1">Wear-related failures such as jaw plate wear and bearing failures constitute more than 60% of breakdowns</cite> (peer-reviewed source) | 0.70       | None — flagged (thickness-survey wear, not vibration-detectable) |
| Toggle plate / toggle seat                     | <cite index="22-1">Toggle seat cracking happens suddenly between shifts</cite>, structural fatigue rather than gradual wear | 0.60       | None — flagged (visual/periodic inspection, not vibration-detectable) |
| Drive motor bearing                            | Motor bearing wear is a standard rotating-machinery fault, generally more replaceable than the eccentric shaft | 0.65       | Real (CWRU bearing proxy) |
| Countershaft bearing                           | <cite index="21-1">Countershaft bearing temperature is tracked alongside main and eccentric bearings as a lubrication-failure indicator</cite> | 0.55       | Real (CWRU bearing proxy) |
| CSS (closed-side setting) / setting mechanism  | <cite index="21-1">CSS drift reflects liner wear, eccentric wear, or setting mechanism wear, with a 4-8 week detection window</cite> | 0.40       | None — flagged (hydraulic/geometric drift, not vibration-detectable) |

Supporting figures worth citing in your business case: <cite index="17-1">56% of premature bearing failures in cement crusher systems are lubrication-related and preventable</cite>, and <cite index="19-1">an unplanned primary crusher failure can cost a plant $120,000-$350,000 per day in lost production</cite> — the latter figure should be treated as an industry-wide estimate, not a DCP-specific one, per Assumption 4.

---

## 4. Detection Confidence Weight (unchanged)

```
margin = P(predicted class) - P(second most likely class)
W_detection = 0.5 + 0.5 x margin
```

---

## 5. Risk Tiers and Recommended Actions (unchanged)

| Risk Score | Tier         | Recommended Action                                                    |
|:----------:|--------------|------------------------------------------------------------------------|
| 80 - 100   | **Critical** | Immediate inspection; plan controlled stop                              |
| 55 - 79    | **High**     | Schedule inspection within 1-2 weeks; increase monitoring frequency      |
| 30 - 54    | **Medium**   | Add to next planned maintenance window; monitor trend                    |
| 0 - 29     | **Low**      | No action; continue routine monitoring                                   |

For unmodeled components, recommend a **thickness-survey or visual-inspection
interval** instead of a live risk score — e.g. <cite index="19-1">jaw plate wear is fully predictable, with wear rate per tonne processed essentially constant for a given rock hardness, giving a 3-4 week gap between order-trigger thickness and condemn limit</cite> that a fixed inspection schedule can track directly.

---

## 6. Why This Framework Matters

- **Strongest citation quality of the four equipment frameworks so far** —
  grounded partly in a peer-reviewed MTBF/MTTR study, not only vendor content.
- Maintains the same "bearing-modeled vs. wear-flagged" honesty pattern as
  mills and packing — the crusher's highest-severity *wear* component (jaw
  plate, tied to 60%+ of breakdowns) is deliberately NOT given a fabricated
  vibration-based score, since that would overstate what the model can do.
- Same scoring architecture, same trained CWRU model reused wherever bearing
  physics genuinely applies — completing a four-equipment-class reliability
  engine (kiln, mill, packing, crusher) built on one consistent method.
