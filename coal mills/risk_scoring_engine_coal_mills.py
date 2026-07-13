"""
Reliability Risk Scoring Engine — COAL MILL VERSION (Mechanical Scope Only)
-------------------------------------------------------------------------------
Covers only the mechanical/reliability components -- see
reliability_framework_coal_mills.md Section 6 for why fire/explosion risk
(CO, O2, mill outlet temperature) is deliberately excluded from this scoring
model and treated as a separate safety layer.

- CWRU-trained Random Forest -> bearing components (main/roller, classifier,
  rotary feeder, seal air fan)
- Gearbox-trained Random Forest -> girth gear / pinion / gearbox
- Grinding table/rollers (VRM) and mill liners -> unmodeled, severity-only

Risk Score = P_fault x W_severity x W_detection x 100

Outputs:
  - /home/claude/risk_scores_coal_mills.csv
  - /home/claude/unmodeled_components_coal_mills.csv
  - /home/claude/risk_matrix_coal_mills.png
  - /home/claude/risk_tier_distribution_coal_mills.png
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

CWRU_PATH = "/home/claude/cwru_features.csv"
GEARBOX_PATH = "/home/claude/gearbox_features.csv"
RANDOM_STATE = 42

CWRU_FEATURE_COLS = [
    "mean", "std", "rms", "peak", "peak_to_peak", "kurtosis", "skewness",
    "crest_factor", "shape_factor", "impulse_factor",
    "fft_band_1_energy", "fft_band_2_energy", "fft_band_3_energy",
    "fft_band_4_energy", "fft_band_5_energy", "fft_dominant_freq", "fft_total_energy"
]

BEARING_COMPONENTS = {
    "Main / Grinding Roller Bearing":       1.00,
    "Classifier / Separator Drive Bearing": 0.55,
    "Rotary Feeder Bearing":                0.45,
    "Seal Air Fan Bearing":                 0.35,
}
GEARBOX_COMPONENT = {"Girth Gear / Pinion / Gearbox": 0.95}

UNMODELED_COMPONENTS = {
    "Grinding Table / Rollers (VRM)": 0.80,
    "Mill Liners":                    0.55,
}

RISK_TIERS = [
    (80, 100, "Critical"), (55, 79.999, "High"),
    (30, 54.999, "Medium"), (0, 29.999, "Low"),
]


def risk_tier(score):
    for low, high, label in RISK_TIERS:
        if low <= score <= high:
            return label
    return "Low"


def compute_detection_weight(proba_row):
    sorted_probs = np.sort(proba_row)[::-1]
    margin = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) > 1 else sorted_probs[0]
    return 0.5 + 0.5 * margin


def score_bearing_readings(rng):
    df = pd.read_csv(CWRU_PATH).dropna(subset=CWRU_FEATURE_COLS + ["fault_type"])
    X, y = df[CWRU_FEATURE_COLS], df["fault_type"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
    )
    rf = RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE, class_weight="balanced")
    rf.fit(X_train, y_train)

    proba = rf.predict_proba(X_test)
    classes = rf.classes_
    normal_idx = list(classes).index("Normal")
    p_fault = 1 - proba[:, normal_idx]
    w_detection = np.array([compute_detection_weight(row) for row in proba])

    equipment_options = list(BEARING_COMPONENTS.keys())
    equipment_assignment = rng.choice(equipment_options, size=len(X_test))
    w_severity = np.array([BEARING_COMPONENTS[e] for e in equipment_assignment])

    return pd.DataFrame({
        "model_source": "CWRU (bearing proxy)",
        "equipment": equipment_assignment,
        "true_label": y_test.values,
        "P_fault": p_fault,
        "W_severity": w_severity,
        "W_detection": w_detection,
    })


def score_gearbox_readings():
    df = pd.read_csv(GEARBOX_PATH)
    feature_cols = [c for c in df.columns if c not in ("condition", "load_pct", "source_file")]
    X, y = df[feature_cols], df["condition"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
    )
    rf = RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE, class_weight="balanced")
    rf.fit(X_train, y_train)

    proba = rf.predict_proba(X_test)
    classes = rf.classes_
    healthy_idx = list(classes).index("Healthy")
    p_fault = 1 - proba[:, healthy_idx]
    w_detection = np.array([compute_detection_weight(row) for row in proba])

    equipment_name = list(GEARBOX_COMPONENT.keys())[0]
    w_severity = np.full(len(X_test), GEARBOX_COMPONENT[equipment_name])

    return pd.DataFrame({
        "model_source": "Gearbox dataset (real gear-fault proxy)",
        "equipment": equipment_name,
        "true_label": y_test.values,
        "P_fault": p_fault,
        "W_severity": w_severity,
        "W_detection": w_detection,
    })


def main():
    rng = np.random.default_rng(RANDOM_STATE)

    bearing_results = score_bearing_readings(rng)
    gearbox_results = score_gearbox_readings()

    combined = pd.concat([bearing_results, gearbox_results], ignore_index=True)
    combined["risk_score"] = combined["P_fault"] * combined["W_severity"] * combined["W_detection"] * 100
    combined["risk_tier"] = combined["risk_score"].apply(risk_tier)

    combined.to_csv("/home/claude/risk_scores_coal_mills.csv", index=False)

    unmodeled = pd.DataFrame([
        {"equipment": name, "W_severity": sev, "status": "No trained model -- severity-ranked only",
         "note": "No matching public sensor dataset found for this failure mode"}
        for name, sev in UNMODELED_COMPONENTS.items()
    ])
    unmodeled.to_csv("/home/claude/unmodeled_components_coal_mills.csv", index=False)

    print(f"Scored {len(combined)} readings across {combined['equipment'].nunique()} modeled components.\n")
    print("By equipment:")
    print(combined.groupby("equipment")["risk_score"].agg(["mean", "max", "count"]))
    print("\nRisk tier distribution:")
    print(combined["risk_tier"].value_counts())
    print("\nUnmodeled components (severity-only, no P_fault):")
    print(unmodeled.to_string(index=False))
    print("\nNOTE: Fire/explosion safety indicators (CO, O2, mill outlet temp) are "
          "OUT OF SCOPE for this scoring model by design -- see framework doc Section 6.")

    tier_colors = {"Critical": "#c0392b", "High": "#e67e22", "Medium": "#f1c40f", "Low": "#2ecc71"}
    markers = {"CWRU (bearing proxy)": "o", "Gearbox dataset (real gear-fault proxy)": "^"}
    fig, ax = plt.subplots(figsize=(8, 6))
    for source, marker in markers.items():
        subset_source = combined[combined["model_source"] == source]
        for tier, color in tier_colors.items():
            subset = subset_source[subset_source["risk_tier"] == tier]
            ax.scatter(subset["P_fault"], subset["W_severity"], c=color, marker=marker, alpha=0.5, s=25)
    from matplotlib.lines import Line2D
    tier_handles = [Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=8, label=t)
                    for t, c in tier_colors.items()]
    source_handles = [Line2D([0], [0], marker=m, color='gray', linestyle='', markersize=8, label=s.split(' (')[0])
                       for s, m in markers.items()]
    ax.legend(handles=tier_handles + source_handles, loc="center right", fontsize=8)
    ax.set_xlabel("P(fault) — model predicted probability")
    ax.set_ylabel("Severity weight (coal mill component criticality)")
    ax.set_title("Coal Mill Risk Matrix (Mechanical Scope): Circles=Bearing, Triangles=Gearbox")
    plt.tight_layout()
    plt.savefig("/home/claude/risk_matrix_coal_mills.png", dpi=150)
    plt.close()

    fig, ax = plt.subplots(figsize=(6, 5))
    tier_order = ["Low", "Medium", "High", "Critical"]
    counts = combined["risk_tier"].value_counts().reindex(tier_order, fill_value=0)
    colors = [tier_colors[t] for t in tier_order]
    ax.bar(tier_order, counts.values, color=colors)
    ax.set_title("Distribution of Coal Mill Readings by Risk Tier")
    ax.set_ylabel("Number of readings")
    plt.tight_layout()
    plt.savefig("/home/claude/risk_tier_distribution_coal_mills.png", dpi=150)
    plt.close()

    print("\nSaved: risk_scores_coal_mills.csv, unmodeled_components_coal_mills.csv, "
          "risk_matrix_coal_mills.png, risk_tier_distribution_coal_mills.png")


if __name__ == "__main__":
    main()
