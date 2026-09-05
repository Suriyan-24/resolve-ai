import pytest
from app.db.session import SessionLocal, init_db
from app.db.repositories import DisputeRepository
from app.tools.dispute_tools import DisputeToolRegistry
from app.services.agent_service import AIAgentInvestigator, AgentInvestigationResult
from scripts.seed_db import seed_database

@pytest.fixture(scope="module", autouse=True)
def setup_seeded_database():
    seed_database()

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_dispute_tool_registry_methods(db_session):
    dispute_repo = DisputeRepository(db_session)
    disputes = dispute_repo.list_disputes(limit=1)
    assert len(disputes) > 0

    dispute = disputes[0]
    tools = DisputeToolRegistry(db_session)

    # 1. get_transaction
    tx_info = tools.get_transaction(dispute.id)
    assert "amount" in tx_info
    assert "payment_method" in tx_info

    # 2. get_customer_history
    cust_info = tools.get_customer_history(dispute.transaction.customer_id)
    assert "email" in cust_info
    assert "total_orders" in cust_info

    # 3. get_order_and_delivery
    order_info = tools.get_order_and_delivery(dispute.transaction_id)
    assert "delivery_status" in order_info

    # 4. get_previous_disputes
    prev_disputes = tools.get_previous_disputes(dispute.transaction.customer_id)
    assert "disputes" in prev_disputes

    # 5. get_risk_analysis
    risk_info = tools.get_risk_analysis(dispute.id)
    assert "risk_score" in risk_info
    assert "risk_level" in risk_info


def test_ai_agent_investigation_end_to_end(db_session):
    dispute_repo = DisputeRepository(db_session)
    disputes = dispute_repo.list_disputes(limit=5)
    assert len(disputes) >= 3

    investigator = AIAgentInvestigator(db_session)

    for dispute in disputes:
        res = investigator.investigate(dispute.id)
        assert isinstance(res, AgentInvestigationResult)
        assert res.dispute_id == dispute.id
        assert res.recommendation in ["DEFEND", "REVIEW", "ACCEPT"]
        assert 0.0 <= res.confidence <= 1.0
        assert len(res.tool_traces) == 5
        assert res.summary is not None


def test_ai_agent_fallback_behavior(db_session):
    investigator = AIAgentInvestigator(db_session)
    invalid_id = "non_existent_dispute_id_12345"

    res = investigator.investigate(invalid_id)
    assert res.recommendation == "REVIEW"
    assert res.confidence == 0.50
    assert "investigation aborted" in res.summary.lower() or "fallback" in res.summary.lower()
    assert res.human_approval_required is True
