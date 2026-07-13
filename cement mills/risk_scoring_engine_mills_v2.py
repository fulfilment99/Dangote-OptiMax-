"""
Reliability Risk Scoring Engine — MILL VERSION v2
-----------------------------------------------------
Combines TWO real, independently-trained models into one unified risk score:
  - CWRU-trained Random Forest -> bearing components (trunnion, motor, fan, separator)
  - Gearbox-trained Random Forest -> girth gear / pinion / gearbox component

Mill Shell Liners and Grinding Table/Rollers (VRM) have NO trained model
backing them (no matching public dataset found) -- these are reported
separately as severity-only flags, not blended into the same scored table,
so a reader can't mistake them for real model output.

Risk Score = P_fault x W_severity x W_detection x 100

See reliability_framework_mills_v2.md Section 0 for full assumptions.

Outputs:
  - /home/claude/risk_scores_mills_v2.csv       (modeled components only)
  - /home/claude/unmodeled_components_mills.csv (liner + VRM table, severity-only)
  - /home/claude/risk_matrix_mills_v2.png
  - /home/claude/risk_tier_distribution_mills_v2.png
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
    "Trunnion Bearing (Ball Mill)": 1.00,
    "Main Drive Motor Bearing":     0.50,
    "Mill Fan / Auxiliary Bearing": 0.25,
    "Separator Bearing":            0.30,
}
GEARBOX_COMPONENT = {"Girth Gear / Pinion / Gearbox": 0.95}

UNMODELED_COMPONENTS = {
    "Mill Shell Liners":               0.55,
    "Grinding Table / Rollers (VRM)":  0.80,
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
    """Train CWRU model, score test set, assign to bearing components."""
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
    """Train gearbox model, score test set, assign to gearbox component."""
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

    combined.to_csv("/home/claude/risk_scores_mills_v2.csv", index=False)

    # Unmodeled components -- reported separately, no P_fault
    unmodeled = pd.DataFrame([
        {"equipment": name, "W_severity": sev, "status": "No trained model -- severity-ranked only",
         "note": "No matching public sensor dataset found for this failure mode"}
        for name, sev in UNMODELED_COMPONENTS.items()
    ])
    unmodeled.to_csv("/home/claude/unmodeled_components_mills.csv", index=False)

    print(f"Scored {len(combined)} readings across {combined['equipment'].nunique()} modeled components.\n")
    print("By model source:")
    print(combined.groupby("model_source")["risk_score"].agg(["mean", "count"]))
    print("\nBy equipment:")
    print(combined.groupby("equipment")["risk_score"].agg(["mean", "max", "count"]))
    print("\nRisk tier distribution:")
    print(combined["risk_tier"].value_counts())
    print("\nUnmodeled components (severity-only, no P_fault):")
    print(unmodeled.to_string(index=False))

    # --- Plot 1: Risk matrix, colored by tier, marker shape by model source ---
    tier_colors = {"Critical": "#c0392b", "High": "#e67e22", "Medium": "#f1c40f", "Low": "#2ecc71"}
    markers = {"CWRU (bearing proxy)": "o", "Gearbox dataset (real gear-fault proxy)": "^"}
    fig, ax = plt.subplots(figsize=(8, 6))
    for source, marker in markers.items():
        subset_source = combined[combined["model_source"] == source]
        for tier, color in tier_colors.items():
            subset = subset_source[subset_source["risk_tier"] == tier]
            ax.scatter(subset["P_fault"], subset["W_severity"], c=color, marker=marker,
                       alpha=0.5, s=25, label=f"{tier} ({source.split(' ')[0]})" if False else None)
    # Build a cleaner combined legend manually
    from matplotlib.lines import Line2D
    tier_handles = [Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=8, label=t)
                    for t, c in tier_colors.items()]
    source_handles = [Line2D([0], [0], marker=m, color='gray', linestyle='', markersize=8, label=s.split(' (')[0])
                       for s, m in markers.items()]
    ax.legend(handles=tier_handles + source_handles, loc="center right", fontsize=8)
    ax.set_xlabel("P(fault) — model predicted probability")
    ax.set_ylabel("Severity weight (mill component criticality)")
    ax.set_title("Risk Matrix (v2): Circles = Bearing Model, Triangles = Gearbox Model")
    plt.tight_layout()
    plt.savefig("/home/claude/risk_matrix_mills_v2.png", dpi=150)
    plt.close()

    # --- Plot 2: Risk tier distribution ---
    fig, ax = plt.subplots(figsize=(6, 5))
    tier_order = ["Low", "Medium", "High", "Critical"]
    counts = combined["risk_tier"].value_counts().reindex(tier_order, fill_value=0)
    colors = [tier_colors[t] for t in tier_order]
    ax.bar(tier_order, counts.values, color=colors)
    ax.set_title("Distribution of Mill Readings by Risk Tier (v2 - Dual Model)")
    ax.set_ylabel("Number of readings")
    plt.tight_layout()
    plt.savefig("/home/claude/risk_tier_distribution_mills_v2.png", dpi=150)
    plt.close()

    print("\nSaved: risk_scores_mills_v2.csv, unmodeled_components_mills.csv, "
          "risk_matrix_mills_v2.png, risk_tier_distribution_mills_v2.png")


if __name__ == "__main__":
    main()
