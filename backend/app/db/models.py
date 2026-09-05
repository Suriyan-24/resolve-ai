import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, Boolean, DateTime, ForeignKey, 
    Text, JSON, Numeric, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), nullable=False, index=True)
    account_created_at = Column(DateTime, default=utc_now, nullable=False)
    total_orders = Column(Numeric(10, 0), default=0)
    historical_disputes = Column(Numeric(10, 0), default=0)

    transactions = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer id={self.id} email={self.email}>"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    razorpay_payment_id = Column(String(100), unique=True, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    payment_method = Column(String(50), nullable=False)
    device_fingerprint = Column(String(100), nullable=False)
    ip_country = Column(String(10), default="IN", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    customer = relationship("Customer", back_populates="transactions")
    order = relationship("Order", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    disputes = relationship("Dispute", back_populates="transaction", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Transaction id={self.id} payment_id={self.razorpay_payment_id} amount={self.amount}>"


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    delivery_status = Column(String(50), nullable=False, default="DELIVERED")
    tracking_number = Column(String(100), nullable=True)
    carrier_delivered_at = Column(DateTime, nullable=True)
    shipping_address_hash = Column(String(100), nullable=True)

    transaction = relationship("Transaction", back_populates="order")

    def __repr__(self):
        return f"<Order id={self.id} status={self.delivery_status}>"


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    razorpay_dispute_id = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="OPEN", index=True)  # OPEN, UNDER_REVIEW, DEFENDED, ACCEPTED
    dispute_amount = Column(Float, nullable=False)
    reason_code = Column(String(100), nullable=False)  # merchandise_not_received, unauthorized, item_damaged
    respond_by = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    transaction = relationship("Transaction", back_populates="disputes")
    risk_scores = relationship("RiskScore", back_populates="dispute", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="dispute", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="dispute", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="dispute", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Dispute id={self.id} razorpay_dispute_id={self.razorpay_dispute_id} status={self.status}>"


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dispute_id = Column(String(36), ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)  # 0.0 to 1.0
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH
    feature_contributions = Column(JSON, default=dict)
    model_version = Column(String(50), default="v1.0.0", nullable=False)
    calculated_at = Column(DateTime, default=utc_now, nullable=False)

    dispute = relationship("Dispute", back_populates="risk_scores")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dispute_id = Column(String(36), ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_type = Column(String(50), nullable=False)  # delivery_confirmation, ip_match, device_fingerprint, past_history
    evidence_metadata = Column(JSON, default=dict)
    verified = Column(Boolean, default=True, nullable=False)
    assembled_at = Column(DateTime, default=utc_now, nullable=False)

    dispute = relationship("Dispute", back_populates="evidence")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dispute_id = Column(String(36), ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation = Column(String(20), nullable=False)  # DEFEND, REVIEW, ACCEPT
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    executive_summary = Column(Text, nullable=False)
    supporting_evidence = Column(JSON, default=list)
    contradicting_evidence = Column(JSON, default=list)
    human_approval_required = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    dispute = relationship("Dispute", back_populates="decisions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dispute_id = Column(String(36), ForeignKey("disputes.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_type = Column(String(50), nullable=False)  # SYSTEM, AI_AGENT, HUMAN_USER
    actor_id = Column(String(100), nullable=False)
    action_taken = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

    dispute = relationship("Dispute", back_populates="audit_logs")


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(100), unique=True, nullable=False, index=True)  # Deduplication index
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, default=dict)
    processed = Column(Boolean, default=False, nullable=False, index=True)
    received_at = Column(DateTime, default=utc_now, nullable=False)
