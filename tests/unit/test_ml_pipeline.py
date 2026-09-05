import pytest
from ml.risk_engine import MLRiskEngine
from ml.interfaces import RiskScoreResult

@pytest.fixture
def risk_engine():
    return MLRiskEngine()

def test_ml_risk_engine_inference(risk_engine):
    # Test High-risk scenario (device mismatch + IP country mismatch)
    high_risk_features = {
        "transaction_amount": 12500.0,
        "account_age_days": 10,
        "previous_orders": 1,
        "previous_disputes": 2,
        "refund_count_30d": 3,
        "carrier_delivery_gap_hours": 120.0,
        "device_change_flag": True,
        "ip_country_mismatch": True,
        "order_velocity_24h": 4,
        "amount_vs_historical_avg_ratio": 4.5,
        "delivery_confirmation_valid": False
    }

    result = risk_engine.predict_risk(high_risk_features)
    assert isinstance(result, RiskScoreResult)
    assert result.risk_score >= 0.70
    assert result.risk_level == "HIGH"
    assert "device_change_flag" in result.feature_contributions
    assert result.model_version == "v1.0.0"

def test_ml_risk_engine_low_risk(risk_engine):
    # Test Low-risk scenario (consistent device, matching IP, verified delivery)
    low_risk_features = {
        "transaction_amount": 800.0,
        "account_age_days": 365,
        "previous_orders": 25,
        "previous_disputes": 0,
        "refund_count_30d": 0,
        "carrier_delivery_gap_hours": 24.0,
        "device_change_flag": False,
        "ip_country_mismatch": False,
        "order_velocity_24h": 1,
        "amount_vs_historical_avg_ratio": 1.0,
        "delivery_confirmation_valid": True
    }

    result = risk_engine.predict_risk(low_risk_features)
    assert isinstance(result, RiskScoreResult)
    assert result.risk_score < 0.35
    assert result.risk_level == "LOW"
