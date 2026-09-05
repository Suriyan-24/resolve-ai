from ml.interfaces import AbstractRiskEngine, RiskScoreResult
from typing import Dict, Any

class MockRiskEngine(AbstractRiskEngine):
    def predict_risk(self, features: Dict[str, Any]) -> RiskScoreResult:
        score = 0.85 if features.get("device_changed", False) else 0.15
        return RiskScoreResult(
            risk_score=score,
            risk_level="HIGH" if score > 0.70 else "LOW",
            feature_contributions={"device_changed": score}
        )

def test_mock_risk_engine_contract():
    engine = MockRiskEngine()
    result = engine.predict_risk({"device_changed": True})
    
    assert isinstance(result, RiskScoreResult)
    assert result.risk_score == 0.85
    assert result.risk_level == "HIGH"
    assert "device_changed" in result.feature_contributions
