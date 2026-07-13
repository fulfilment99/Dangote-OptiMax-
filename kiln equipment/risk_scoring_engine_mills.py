import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# --- 1. UPDATE YOUR FILE PATHS HERE ---
# Put your Excel file in the same folder as this script, or paste the full path
DATA_PATH = "cwru_features.xlsx"

FEATURE_COLS = [
    "mean", "std", "rms", "peak", "peak_to_peak", "kurtosis", "skewness",
    "crest_factor", "shape_factor", "impulse_factor",
    "fft_band_1_energy", "fft_band_2_energy", "fft_band_3_energy",
    "fft_band_4_energy", "fft_band_5_energy", "fft_dominant_freq", "fft_total_energy"
]

SEVERITY_WEIGHTS = {
    "Trunnion Bearing (Ball Mill)": 1.00,
    "Girth Gear / Pinion / Gearbox": 0.95,
    "Grinding Table / Rollers (VRM)": 0.80,
    "Mill Shell Liners": 0.55,
    "Main Drive Motor Bearing": 0.50,
    "Separator Bearing": 0.30,
    "Mill Fan / Auxiliary Bearing": 0.25,
}

RISK_TIERS = [
    (80, 100, "Critical"),
    (55, 79.999, "High"),
    (30, 54.999, "Medium"),
    (0, 29.999, "Low"),
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
    # --- 2. CHANGED TO READ EXCEL ---
    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_excel(DATA_PATH).dropna(subset=FEATURE_COLS + ["fault_type"])

    X = df[FEATURE_COLS]
    y = df["fault_type"]

    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, df.index, test_size=0.25, random_state=42, stratify=y
    )

    print("Training Random Forest model...")
    rf = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
    rf.fit(X_train, y_train)

    proba = rf.predict_proba(X_test)
    classes = rf.classes_
    normal_idx = list(classes).index("Normal")
    preds = rf.predict(X_test)

    p_fault = 1 - proba[:, normal_idx]
    w_detection = np.array([compute_detection_weight(row) for row in proba])

    rng = np.random.default_rng(42)
    equipment_options = list(SEVERITY_WEIGHTS.keys())
    equipment_assignment = rng.choice(equipment_options, size=len(X_test))
    w_severity = np.array([SEVERITY_WEIGHTS[e] for e in equipment_assignment])

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

    # --- 3. OUTPUTS SAVED TO CURRENT DIRECTORY ---
    results.to_csv("risk_scores_mills.csv", index=False)
    print("\nScored results saved to 'risk_scores_mills.csv'")

    print(f"\nScored {len(results)} readings.")
    print("\nRisk Tier distribution:")
    print(results["risk_tier"].value_counts())
    print("\nMean risk score by equipment:")
    print(results.groupby("equipment")["risk_score"].agg(["mean", "max", "count"]))

    # Plot 1: Risk matrix
    tier_colors = {"Critical": "#c0392b", "High": "#e67e22", "Medium": "#f1c40f", "Low": "#2ecc71"}
    fig, ax = plt.subplots(figsize=(8, 6))
    for tier, color in tier_colors.items():
        subset = results[results["risk_tier"] == tier]
        ax.scatter(subset["P_fault"], subset["W_severity"], c=color, label=tier, alpha=0.5, s=15)
    ax.set_xlabel("P(fault) — model predicted probability")
    ax.set_ylabel("Severity weight (mill component criticality)")
    ax.set_title("Risk Matrix: Fault Probability x Mill Component Severity")
    ax.legend(title="Risk Tier")
    plt.tight_layout()
    plt.savefig("risk_matrix_mills.png", dpi=150)
    plt.close()
    print("Saved 'risk_matrix_mills.png'")

    # Plot 2: Risk tier distribution
    fig, ax = plt.subplots(figsize=(7, 5))
    tier_order = ["Critical", "High", "Medium", "Low"]
    tier_counts = results["risk_tier"].value_counts().reindex(tier_order, fill_value=0)
    colors = [tier_colors[tier] for tier in tier_order]

    bars = ax.bar(tier_counts.index, tier_counts.values, color=colors, edgecolor="black", alpha=0.8)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{int(height)}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')

    ax.set_xlabel("Risk Tier")
    ax.set_ylabel("Count of Readings")
    ax.set_title("Distribution of Risk Tiers Across Mill Components")
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig("risk_tier_distribution_mills.png", dpi=150)
    plt.close()
    print("Saved 'risk_tier_distribution_mills.png'")


if __name__ == "__main__":
    main()


