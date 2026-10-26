import os
from typing import Dict, Any

from ml.interfaces import AbstractRiskEngine, RiskScoreResult
from app.core.logging import logger

FEATURE_COLUMNS = [
    "transaction_amount",
    "account_age_days",
    "previous_orders",
    "previous_disputes",
    "refund_count_30d",
    "carrier_delivery_gap_hours",
    "device_change_flag",
    "ip_country_mismatch",
    "order_velocity_24h",
    "amount_vs_historical_avg_ratio",
    "delivery_confirmation_valid"
]


class MLRiskEngine(AbstractRiskEngine):
    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), "models", "risk_model_v1.joblib")
        self.model_path = model_path
        self.model = None
        self.feature_columns = FEATURE_COLUMNS
        self.model_version = "v1.0.0"
        self._load_model()

    def _load_model(self):
        if not os.path.exists(self.model_path):
            logger.warning("No trained model found. Using fallback deterministic risk calculation.")
            return
        try:
            import joblib
            payload = joblib.load(self.model_path)
            self.model = payload["model"]
            self.feature_columns = payload.get("feature_columns", FEATURE_COLUMNS)
            self.model_version = payload.get("model_version", "v1.0.0")
            logger.info("Loaded trained ML Risk Engine from %s", self.model_path)
        except Exception as exc:
            logger.warning("Could not load trained model; using fallback risk calculation: %s", exc)
            self.model = None

    def _extract_feature_vector(self, features: Dict[str, Any]):
        return [
            float(features.get("transaction_amount", 1000.0)),
            float(features.get("account_age_days", 30)),
            float(features.get("previous_orders", 1)),
            float(features.get("previous_disputes", 0)),
            float(features.get("refund_count_30d", 0)),
            float(features.get("carrier_delivery_gap_hours", 48.0)),
            float(bool(features.get("device_change_flag", False))),
            float(bool(features.get("ip_country_mismatch", False))),
            float(features.get("order_velocity_24h", 1)),
            float(features.get("amount_vs_historical_avg_ratio", 1.0)),
            float(bool(features.get("delivery_confirmation_valid", True)))
        ]

    def predict_risk(self, features: Dict[str, Any]) -> RiskScoreResult:
        vector = self._extract_feature_vector(features)
        risk_score = None

        if self.model is not None:
            try:
                import pandas as pd
                df_vector = pd.DataFrame([vector], columns=self.feature_columns)
                probs = self.model.predict_proba(df_vector)[0]
                risk_score = float(probs[1])
            except Exception as exc:
                logger.warning("Trained model prediction failed; using fallback: %s", exc)

        if risk_score is None:
            score = 0.20
            if features.get("device_change_flag"):
                score += 0.35
            if features.get("ip_country_mismatch"):
                score += 0.30
            if not features.get("delivery_confirmation_valid", True):
                score += 0.25
            if features.get("previous_disputes", 0) > 1:
                score += 0.20
            risk_score = min(0.99, max(0.01, score))

        risk_score = round(risk_score, 4)
        if risk_score >= 0.70:
            risk_level = "HIGH"
        elif risk_score >= 0.35:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        feature_contributions = {
            "device_change_flag": 0.40 if features.get("device_change_flag") else 0.0,
            "ip_country_mismatch": 0.35 if features.get("ip_country_mismatch") else 0.0,
            "delivery_confirmation_valid": -0.45 if features.get("delivery_confirmation_valid") else 0.30,
            "previous_disputes": round(min(0.30, features.get("previous_disputes", 0) * 0.10), 2),
            "amount_vs_avg_ratio": round(min(0.25, features.get("amount_vs_historical_avg_ratio", 1.0) * 0.05), 2)
        }
        return RiskScoreResult(
            risk_score=risk_score,
            risk_level=risk_level,
            feature_contributions=feature_contributions,
            model_version=self.model_version
        )
