# Reliability Early-Warning Framework & Risk Scoring Model
## Raw Mill Predictive Maintenance — DCP University Engineering Challenge, Track 2

---

## 0. Explicit Assumptions

1. **This framework leads with Vertical Roller Mill (VRM) as the primary
   reference type — the reverse emphasis from the cement mill framework**,
   because <cite index="37-1">over the last three decades the vertical roller mill has become the preferred mill for grinding of raw materials</cite>, and <cite index="36-1">the vertical roller mill has become the dominant choice for new raw material grinding systems due to its low power consumption and ease of operation, efficiently grinding hard, abrasive, high-moisture-content material</cite>. This is the opposite emphasis from the cement mill document, which correctly led with ball mill since <cite index="37-1">the ball mill is still today the most used mill for cement grinding</cite>, even as VRM adoption grows there too.
2. **This produces the single most important honest gap in this whole
   five-equipment submission**: the raw mill's highest-severity component —
   the grinding table/rollers — is **unmodeled**. No public vibration
   dataset was found for VRM table/roller wear, so your top-severity raw mill
   component has no ML-backed risk score. State this plainly; it is a more
   credible position than quietly reusing a bearing-fault proxy for a
   fundamentally different compression-grinding failure mode.
3. **Raw mills carry a drying function that cement mills generally do not**,
   since <cite index="35-1">raw material mills often use vertical roller mills or air-swept ball mills to cope with high humidity and large particles, and need to take into account drying functions, usually consuming 10-30% more energy than cement mills due to the need for drying and coarse grinding</cite>. This is why the hot-gas mill fan is weighted higher here than in the cement mill framework.
4. **The hydraulic roller-loading system is VRM-specific and unmodeled** —
   it is a hydraulic pressure system, not a rotating bearing, so it does not
   fit the CWRU proxy any more than the grinding table itself does.
5. **Severity weights are literature-derived estimates**, not DCP-confirmed
   figures. Equipment-to-reading assignment remains simulated for modeled
   components, consistent with all prior framework versions.

---

## 1. Framework Overview

```
[1] SENSING          [2] FEATURES        [3] CLASSIFICATION      [4] RISK SCORING     [5] ACTION
Table bearing,    ->  RMS, kurtosis,  ->  CWRU-trained RF     -\                    
fan, separator         FFT bands           (bearing components)   >-  Risk Engine  ->  Alert/work
bearings                                                          /   combines           order with
Girth gear/       ->  Same pipeline   ->  Gearbox-trained RF -/    P(fault) x         priority tier
gearbox                                                            Severity x
                                                                    Detectability
Grinding table/   ->  No sensor data available -> severity-only flag
rollers, hydraulic
loading system
```

---

## 2. Risk Scoring Formula (unchanged)

```
Risk Score = (P_fault x W_severity x W_detection) x 100
```

---

## 3. Raw Mill Equipment Criticality Table

<cite index="34-1">Vertical Roller Mills generally offer superior energy efficiency, higher production capacity, and better drying capability</cite> compared to ball mills for this duty, which is why the table below is structured around VRM components first.

| Raw Mill Component                         | Failure Consequence                                                        | W_severity | Model Backing |
|------------------------------------------------|--------------------------------------------------------------------------------|:----------:|----------------|
| Grinding table / rollers (VRM)                  | <cite index="39-1">The grinding table and rollers form a bed under hydraulic pressure to crush material by compression rather than impact</cite> — this IS the primary failure surface for a raw mill, but has no vibration-dataset proxy | 1.00       | None — flagged (highest-severity, unmodeled component) |
| Girth gear / pinion / gearbox                    | Drives the rotating table; same catastrophic-downtime class as cement mill gearbox | 0.90       | Real (Gearbox dataset — direct match) |
| Main table bearing                               | Large-diameter bearing supporting the full rotating table and material bed load | 0.85       | Real (CWRU bearing proxy) |
| Hydraulic roller-loading system                  | Governs the compression force between rollers and table; a hydraulic pressure system, not a rotating component | 0.70       | None — flagged (hydraulic pressure trend, not vibration-detectable) |
| Mill fan (hot gas draft fan)                     | <cite index="35-1">Raw material mills use hot gas for combined drying and grinding, consuming 10-30% more energy than cement mills for this reason</cite> — fan failure stops both drying and material transport | 0.55       | Real (CWRU bearing proxy) |
| Separator / classifier drive bearing              | <cite index="34-1">Qualified particles are collected as finished product while oversized particles return to the grinding zone</cite> via the separator — failure disrupts raw meal fineness control | 0.50       | Real (CWRU bearing proxy) |
| Nozzle ring / dam ring wear                       | Wear parts controlling gas flow and bed depth around the grinding table | 0.40       | None — flagged (geometric wear, not vibration-detectable) |

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

For the grinding table/rollers specifically — since it is both highest
severity AND unmodeled — recommend the compensating control described in the
literature: <cite index="27-1">predictive models tracking vibration signatures and motor current increases as the rolling surface degrades generate remaining useful life estimates that define shutdown replacement scope weeks in advance</cite>. This is a legitimate Phase 2 extension to name in your submission — motor current signature analysis is a different sensing modality than vibration and could close this specific gap without needing a bearing-style dataset.

---

## 6. Raw Mill vs. Cement Mill vs. Coal Mill: What Changes

| Element                     | Cement Mill                          | Raw Mill                                | Coal Mill                          |
|------------------------------|----------------------------------------|--------------------------------------------|--------------------------------------|
| Primary technology assumed   | Ball mill                              | VRM                                         | VRM or air-swept ball mill            |
| Top-severity component        | Trunnion bearing (modeled)             | Grinding table/rollers (**unmodeled**)      | Main/roller bearing (modeled)         |
| Unique consideration          | None beyond standard grinding duty      | Drying function raises fan criticality       | Fire/explosion safety layer (separate)|
| Classifier/scoring architecture | Identical                            | Identical                                    | Identical (mechanical scope only)     |

This comparison is worth including directly in your Concept Note — it shows
the same reliability engine correctly produces *different* top-priority
components across equipment types, rather than a generic templated output,
which is a meaningful signal that the framework is actually equipment-aware
rather than copy-pasted.

---

## 7. Why This Framework Matters

- Surfaces the most important honest limitation across your entire
  submission: the component that matters most for a modern raw mill has no
  ML-backed detection in this proof-of-concept, and that gap is named
  directly rather than hidden.
- Correctly reflects that raw milling and cement milling are not the same
  problem wearing different labels — different dominant technology, different
  process role (drying vs. fineness), different severity ordering.
