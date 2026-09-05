from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel, Field

class RiskScoreResult(BaseModel):
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Numerical risk score between 0 and 1")
    risk_level: str = Field(..., description="LOW, MEDIUM, or HIGH")
    feature_contributions: Dict[str, float] = Field(default_factory=dict)
    model_version: str = "v1.0.0"

class AbstractRiskEngine(ABC):
    @abstractmethod
    def predict_risk(self, features: Dict[str, Any]) -> RiskScoreResult:
        """Computes deterministic numerical risk score from transaction features."""
        pass
