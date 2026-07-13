"""
Reliability Risk Scoring Engine — PACKING EQUIPMENT VERSION
----------------------------------------------------------------
Same scoring architecture as kiln/mill versions. Only bearing-driven
components (rotary drive, impeller, palletizer servo, conveyor) get a
model-backed P_fault, using the CWRU bearing classifier as a proxy.

Weighing system drift, spout seal wear, and bag applicator misfeeds are
NOT vibration-bearing faults -- see reliability_framework_packing.md
Section 0 -- and are reported separately with no fabricated P_fault.

Risk Score = P_fault x W_severity x W_detection x 100

Outputs:
  - /home/claude/risk_scores_packing.csv
  - /home/claude/unmodeled_components_packing.csv
  - /home/claude/risk_matrix_packing.png
  - /home/claude/risk_tier_distribution_packing.png
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

CWRU_PATH = "/home/claude/cwru_features.csv"
RANDOM_STATE = 42

CWRU_FEATURE_COLS = [
    "mean", "std", "rms", "peak", "peak_to_peak", "kurtosis", "skewness",
    "crest_factor", "shape_factor", "impulse_factor",
    "fft_band_1_energy", "fft_band_2_energy", "fft_band_3_energy",
    "fft_band_4_energy", "fft_band_5_energy", "fft_dominant_freq", "fft_total_energy"
]

MODELED_COMPONENTS = {
    "Rotary Drive System (Main Drive Motor Bearing)": 0.80,
    "Impeller / Filling Head Bearing":                 0.75,
    "Palletizer Servo Drive / Gripper Bearing":         0.65,
    "Conveyor Belt / Roller Bearing":                   0.35,
}

UNMODELED_COMPONENTS = {
    "Weighing System / Load Cell (metrology drift)": 0.55,
    "Spout Seal / Cone Wear":                        0.45,
    "Bag Applicator Misfeed Mechanism":              0.30,
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


def main():
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
    preds = rf.predict(X_test)

    p_fault = 1 - proba[:, normal_idx]
    w_detection = np.array([compute_detection_weight(row) for row in proba])

    rng = np.random.default_rng(RANDOM_STATE)
    equipment_options = list(MODELED_COMPONENTS.keys())
    equipment_assignment = rng.choice(equipment_options, size=len(X_test))
    w_severity = np.array([MODELED_COMPONENTS[e] for e in equipment_assignment])

    risk_score = p_fault * w_severity * w_detection * 100
    tiers = [risk_tier(s) for s in risk_score]

    results = pd.DataFrame({
        "true_fault_type": y_test.values,
        "predicted_fault_type": preds,
        "P_fault": p_fault,
        "equipment": equipment_assignment,
        "W_severity": w_severity,
        "W_detection": w_detection,
        "risk_score": risk_score,
        "risk_tier": tiers,
    })
    results.to_csv("/home/claude/risk_scores_packing.csv", index=False)

    unmodeled = pd.DataFrame([
        {"equipment": name, "W_severity": sev, "status": "No trained model -- severity-ranked only",
         "note": "Wear/calibration failure mode, not vibration-bearing-detectable"}
        for name, sev in UNMODELED_COMPONENTS.items()
    ])
    unmodeled.to_csv("/home/claude/unmodeled_components_packing.csv", index=False)

    print(f"Scored {len(results)} readings across {len(MODELED_COMPONENTS)} modeled components.\n")
    print("Mean risk score by equipment:")
    print(results.groupby("equipment")["risk_score"].agg(["mean", "max", "count"]))
    print("\nRisk tier distribution:")
    print(results["risk_tier"].value_counts())
    print("\nUnmodeled components (severity-only, no P_fault):")
    print(unmodeled.to_string(index=False))

    tier_colors = {"Critical": "#c0392b", "High": "#e67e22", "Medium": "#f1c40f", "Low": "#2ecc71"}
    fig, ax = plt.subplots(figsize=(8, 6))
    for tier, color in tier_colors.items():
        subset = results[results["risk_tier"] == tier]
        ax.scatter(subset["P_fault"], subset["W_severity"], c=color, label=tier, alpha=0.5, s=20)
    ax.set_xlabel("P(fault) — model predicted probability")
    ax.set_ylabel("Severity weight (packing component criticality)")
    ax.set_title("Risk Matrix: Fault Probability x Packing Component Severity")
    ax.legend(title="Risk Tier")
    plt.tight_layout()
    plt.savefig("/home/claude/risk_matrix_packing.png", dpi=150)
    plt.close()

    fig, ax = plt.subplots(figsize=(6, 5))
    tier_order = ["Low", "Medium", "High", "Critical"]
    counts = results["risk_tier"].value_counts().reindex(tier_order, fill_value=0)
    colors = [tier_colors[t] for t in tier_order]
    ax.bar(tier_order, counts.values, color=colors)
    ax.set_title("Distribution of Packing Readings by Risk Tier")
    ax.set_ylabel("Number of readings")
    plt.tight_layout()
    plt.savefig("/home/claude/risk_tier_distribution_packing.png", dpi=150)
    plt.close()

    print("\nSaved: risk_scores_packing.csv, unmodeled_components_packing.csv, "
          "risk_matrix_packing.png, risk_tier_distribution_packing.png")


if __name__ == "__main__":
    main()
