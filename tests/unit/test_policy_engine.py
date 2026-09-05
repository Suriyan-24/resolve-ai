import pytest
import uuid
from datetime import datetime, timedelta
from app.db.session import SessionLocal, init_db
from app.db.repositories import CustomerRepository, DisputeRepository
from app.db.models import Transaction, Dispute
from app.services.policy_service import (
    PolicyEngine, ActionRequest, ActionType, 
    ActorType, PolicyOutcome
)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def create_test_dispute(db_session, amount: float = 2100.0, status: str = "OPEN") -> Dispute:
    uid = str(uuid.uuid4())[:8]
    cust_repo = CustomerRepository(db_session)
    customer = cust_repo.create(email=f"policy.user.{uid}@example.com")

    tx = Transaction(
        customer_id=customer.id,
        razorpay_payment_id=f"pay_policy_{uid}",
        amount=amount,
        currency="INR",
        payment_method="UPI",
        device_fingerprint="fp_policy_device",
        ip_country="IN"
    )
    db_session.add(tx)
    db_session.commit()

    dispute_repo = DisputeRepository(db_session)
    dispute = dispute_repo.create_dispute(
        transaction_id=tx.id,
        razorpay_dispute_id=f"disp_policy_{uid}",
        dispute_amount=amount,
        reason_code="merchandise_not_received",
        respond_by=datetime.utcnow() + timedelta(days=7),
        status=status
    )
    return dispute


def test_policy_allowed_automated_defense(db_session):
    dispute = create_test_dispute(db_session, amount=2100.0)
    engine = PolicyEngine(db_session)

    req = ActionRequest(
        dispute_id=dispute.id,
        action=ActionType.DEFEND,
        actor_type=ActorType.AI_AGENT,
        actor_id="ResolveAI_Agent_v1",
        risk_score=0.12,
        dispute_amount=2100.0,
        ai_confidence=0.96,
        supporting_evidence=["Proof of Delivery", "Device Match"]
    )

    res = engine.execute_action(req)
    assert res.outcome == PolicyOutcome.ALLOWED
    assert res.executed is True
    assert res.new_status == "DEFENDED"


def test_policy_requires_human_approval_financial_ceiling(db_session):
    dispute = create_test_dispute(db_session, amount=8499.0)
    engine = PolicyEngine(db_session)

    req = ActionRequest(
        dispute_id=dispute.id,
        action=ActionType.DEFEND,
        actor_type=ActorType.AI_AGENT,
        actor_id="ResolveAI_Agent_v1",
        risk_score=0.15,
        dispute_amount=8499.0,
        ai_confidence=0.95,
        supporting_evidence=["Proof of Delivery"]
    )

    res = engine.execute_action(req)
    assert res.outcome == PolicyOutcome.REQUIRES_HUMAN_APPROVAL
    assert res.executed is False
    assert res.new_status == "UNDER_REVIEW"
    assert "exceeds automated ceiling" in res.reason.lower()


def test_policy_blocked_auto_accept_high_risk(db_session):
    dispute = create_test_dispute(db_session, amount=15000.0)
    engine = PolicyEngine(db_session)

    req = ActionRequest(
        dispute_id=dispute.id,
        action=ActionType.ACCEPT,
        actor_type=ActorType.AI_AGENT,
        actor_id="ResolveAI_Agent_v1",
        risk_score=0.87,
        dispute_amount=15000.0,
        ai_confidence=0.90,
        supporting_evidence=[]
    )

    res = engine.execute_action(req)
    assert res.outcome == PolicyOutcome.BLOCKED
    assert res.executed is False
    assert "prohibited by risk policy" in res.reason.lower()


def test_policy_blocked_missing_evidence(db_session):
    dispute = create_test_dispute(db_session, amount=1200.0)
    engine = PolicyEngine(db_session)

    req = ActionRequest(
        dispute_id=dispute.id,
        action=ActionType.DEFEND,
        actor_type=ActorType.AI_AGENT,
        actor_id="ResolveAI_Agent_v1",
        risk_score=0.10,
        dispute_amount=1200.0,
        ai_confidence=0.95,
        supporting_evidence=[]  # Empty evidence
    )

    res = engine.execute_action(req)
    assert res.outcome == PolicyOutcome.BLOCKED
    assert res.executed is False
    assert "without verified supporting evidence" in res.reason.lower()


def test_policy_human_override_authorization(db_session):
    dispute = create_test_dispute(db_session, amount=8499.0)
    engine = PolicyEngine(db_session)

    req = ActionRequest(
        dispute_id=dispute.id,
        action=ActionType.DEFEND,
        actor_type=ActorType.HUMAN_USER,
        actor_id="merchant_admin_42",
        risk_score=0.87,
        dispute_amount=8499.0,
        ai_confidence=0.90,
        supporting_evidence=["Manual Receipt Verification"]
    )

    res = engine.execute_action(req)
    assert res.outcome == PolicyOutcome.ALLOWED
    assert res.executed is True
    assert res.new_status == "DEFENDED"


def test_policy_idempotency_blocked(db_session):
    dispute = create_test_dispute(db_session, amount=2100.0, status="DEFENDED")
    engine = PolicyEngine(db_session)

    req = ActionRequest(
        dispute_id=dispute.id,
        action=ActionType.DEFEND,
        actor_type=ActorType.HUMAN_USER,
        actor_id="merchant_admin_42",
        risk_score=0.10,
        dispute_amount=2100.0,
        ai_confidence=0.95,
        supporting_evidence=["Proof of Delivery"]
    )

    res = engine.execute_action(req)
    assert res.outcome == PolicyOutcome.BLOCKED
    assert res.executed is False
    assert "already in a finalized state" in res.reason.lower()
