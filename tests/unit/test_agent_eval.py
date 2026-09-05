import pytest
from scripts.evaluate_agent import run_agent_evaluation

def test_agent_and_policy_benchmark_evaluation():
    metrics = run_agent_evaluation()
    assert metrics["ai_accuracy"] == 100.0, "AI Recommendation accuracy must be 100%"
    assert metrics["policy_compliance"] == 100.0, "Policy safety compliance must be 100%"
    assert metrics["avg_latency_ms"] < 500.0, "Average pipeline latency must be under 500ms"
