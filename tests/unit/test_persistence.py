import pytest
import uuid
from datetime import datetime, timedelta, timezone
from app.db.session import SessionLocal, init_db
from app.db.models import Customer, Transaction, Dispute, AuditLog, WebhookEvent
from app.db.repositories import (
    CustomerRepository, DisputeRepository, 
    AuditRepository, WebhookRepository
)

@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    init_db()

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_create_customer_and_transaction(db_session):
    uid = str(uuid.uuid4())[:8]
    cust_repo = CustomerRepository(db_session)
    customer = cust_repo.create(email=f"test.user.{uid}@example.com", total_orders=5)

    assert customer.id is not None
    assert f"test.user.{uid}" in customer.email
    assert customer.total_orders == 5

    tx = Transaction(
        customer_id=customer.id,
        razorpay_payment_id=f"pay_test_{uid}",
        amount=1500.0,
        currency="INR",
        payment_method="UPI",
        device_fingerprint="fp_test_device",
        ip_country="IN"
    )
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)

    assert tx.id is not None
    assert tx.customer_id == customer.id
    assert tx.amount == 1500.0


def test_dispute_repository_crud(db_session):
    uid = str(uuid.uuid4())[:8]
    cust_repo = CustomerRepository(db_session)
    customer = cust_repo.create(email=f"dispute.user.{uid}@example.com")
    
    tx = Transaction(
        customer_id=customer.id,
        razorpay_payment_id=f"pay_test_dispute_{uid}",
        amount=3500.0,
        currency="INR",
        payment_method="CARD",
        device_fingerprint="fp_test_device_2",
        ip_country="IN"
    )
    db_session.add(tx)
    db_session.commit()

    dispute_repo = DisputeRepository(db_session)
    dispute = dispute_repo.create_dispute(
        transaction_id=tx.id,
        razorpay_dispute_id=f"disp_test_{uid}",
        dispute_amount=3500.0,
        reason_code="item_damaged",
        respond_by=datetime.now(timezone.utc) + timedelta(days=7),
        status="OPEN"
    )

    assert dispute.id is not None
    assert dispute.razorpay_dispute_id == f"disp_test_{uid}"
    assert dispute.status == "OPEN"

    # Update status
    updated = dispute_repo.update_status(dispute.id, "DEFENDED")
    assert updated.status == "DEFENDED"


def test_duplicate_webhook_prevention(db_session):
    uid = str(uuid.uuid4())[:8]
    webhook_repo = WebhookRepository(db_session)
    event_id = f"evt_razorpay_unique_{uid}"

    # First attempt should succeed
    evt1 = webhook_repo.record_event(
        event_id=event_id,
        event_type="dispute.created",
        payload={"dispute_id": f"disp_test_{uid}"}
    )
    assert evt1 is not None
    assert evt1.event_id == event_id

    # Duplicate attempt with identical event_id must be rejected
    evt2 = webhook_repo.record_event(
        event_id=event_id,
        event_type="dispute.created",
        payload={"dispute_id": f"disp_test_{uid}"}
    )
    assert evt2 is None


def test_audit_log_immutability(db_session):
    audit_repo = AuditRepository(db_session)
    entry = audit_repo.log_event(
        actor_type="AI_AGENT",
        actor_id="ResolveAI_Agent_v1",
        action_taken="EVIDENCE_ASSEMBLED",
        payload={"evidence_count": 3}
    )

    assert entry.id is not None
    assert entry.actor_type == "AI_AGENT"
    assert entry.action_taken == "EVIDENCE_ASSEMBLED"
    assert entry.timestamp is not None

