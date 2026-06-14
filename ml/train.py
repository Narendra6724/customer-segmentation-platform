"""
ML Training Pipeline — Customer Segmentation
Trains K-Means (k=5) on Annual Income × Spending Score,
persists model.pkl and scaler.pkl for the prediction service.
"""

import os
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "Mall_Customers.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")

N_CLUSTERS = 5
RANDOM_STATE = 42

CLUSTER_LABELS = {
    0: "Average Customers",
    1: "Premium Customers",
    2: "Target Customers",
    3: "Low-value Customers",
    4: "Risk Customers",
}


def load_data() -> pd.DataFrame:
    """Load and validate the Mall Customers dataset."""
    df = pd.read_csv(DATA_PATH)
    print(f"[INFO] Loaded {len(df)} records from {DATA_PATH}")
    return df


def train_model(df: pd.DataFrame):
    """Fit scaler + K-Means and persist artifacts."""
    features = df[["Annual Income (k$)", "Spending Score (1-100)"]].values

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    # Train K-Means
    model = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=10)
    model.fit(X_scaled)

    # Save artifacts
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"[INFO] Model saved  → {MODEL_PATH}")
    print(f"[INFO] Scaler saved → {SCALER_PATH}")

    return model, scaler, X_scaled


def print_summary(model, df: pd.DataFrame):
    """Print cluster distribution summary."""
    df = df.copy()
    df["Cluster"] = model.labels_

    print("\n" + "=" * 50)
    print("  CLUSTER SUMMARY")
    print("=" * 50)

    for cluster_id in sorted(df["Cluster"].unique()):
        subset = df[df["Cluster"] == cluster_id]
        label = CLUSTER_LABELS.get(cluster_id, f"Cluster {cluster_id}")
        print(f"\n  [{cluster_id}] {label}")
        print(f"      Count   : {len(subset)}")
        print(f"      Avg Income  : {subset['Annual Income (k$)'].mean():.1f}k$")
        print(f"      Avg Spending: {subset['Spending Score (1-100)'].mean():.1f}")

    print("\n" + "=" * 50)


def main():
    df = load_data()
    model, scaler, X_scaled = train_model(df)
    print_summary(model, df)
    print("\n[SUCCESS] Training pipeline complete.\n")


if __name__ == "__main__":
    main()
