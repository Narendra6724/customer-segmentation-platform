"""
Model Service — loads trained ML artifacts and exposes a predict() function.
"""

import os
import numpy as np
import joblib

# ---------------------------------------------------------------------------
# Paths to persisted ML artifacts
# ---------------------------------------------------------------------------
_ML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ml")
_MODEL_PATH = os.path.join(_ML_DIR, "model.pkl")
_SCALER_PATH = os.path.join(_ML_DIR, "scaler.pkl")

# ---------------------------------------------------------------------------
# Business-insight mapping
# ---------------------------------------------------------------------------
CLUSTER_INSIGHTS: dict[int, dict] = {
    0: {
        "label": "Average Customers",
        "insight": (
            "These customers have moderate income and moderate spending. "
            "They represent the mainstream segment — consider loyalty programs "
            "to increase their engagement."
        ),
    },
    1: {
        "label": "Premium Customers",
        "insight": (
            "High income and high spending — your most valuable segment. "
            "Offer exclusive perks, early access, and personalized experiences "
            "to retain them."
        ),
    },
    2: {
        "label": "Target Customers",
        "insight": (
            "Low income but high spending. They are enthusiastic buyers — "
            "provide budget-friendly deals and instalment options to keep "
            "them engaged without financial strain."
        ),
    },
    3: {
        "label": "Low-value Customers",
        "insight": (
            "Low income and low spending. Minimal revenue contribution. "
            "Use awareness campaigns and introductory discounts to try "
            "converting them."
        ),
    },
    4: {
        "label": "Risk Customers",
        "insight": (
            "High income but low spending. They can afford more but choose "
            "not to spend. Investigate satisfaction issues and offer "
            "targeted high-value promotions."
        ),
    },
}

# ---------------------------------------------------------------------------
# Lazy-loaded singletons
# ---------------------------------------------------------------------------
_model = None
_scaler = None


def _load_artifacts():
    """Load model and scaler once, raise if not found."""
    global _model, _scaler
    if _model is None or _scaler is None:
        if not os.path.exists(_MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {_MODEL_PATH}. Run ml/train.py first."
            )
        _model = joblib.load(_MODEL_PATH)
        _scaler = joblib.load(_SCALER_PATH)
    return _model, _scaler


def predict(income: float, spending: float) -> dict:
    """
    Predict the customer cluster and return a result dict.

    Parameters
    ----------
    income   : Annual income in k$
    spending : Spending score (1-100)

    Returns
    -------
    dict with keys: cluster, label, insight
    """
    model, scaler = _load_artifacts()
    X = np.array([[income, spending]])
    X_scaled = scaler.transform(X)
    cluster_id: int = int(model.predict(X_scaled)[0])

    info = CLUSTER_INSIGHTS.get(cluster_id, {
        "label": f"Cluster {cluster_id}",
        "insight": "No business insight available for this cluster.",
    })

    return {
        "cluster": cluster_id,
        "label": info["label"],
        "insight": info["insight"],
    }
