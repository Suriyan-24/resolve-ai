from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.models import (
    Customer, Transaction, Order, Dispute, 
    RiskScore, Evidence, Decision, AuditLog, WebhookEvent
)
from app.core.logging import logger

class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, email: str, total_orders: int = 0, historical_disputes: int = 0) -> Customer:
        customer = Customer(
            email=email,
            total_orders=total_orders,
            historical_disputes=historical_disputes
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def get_by_email(self, email: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.email == email).first()


class DisputeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, dispute_id: str) -> Optional[Dispute]:
        return self.db.query(Dispute).filter(Dispute.id == dispute_id).first()

    def get_by_razorpay_id(self, razorpay_dispute_id: str) -> Optional[Dispute]:
        return self.db.query(Dispute).filter(Dispute.razorpay_dispute_id == razorpay_dispute_id).first()

    def list_disputes(self, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dispute]:
        query = self.db.query(Dispute)
        if status:
            query = query.filter(Dispute.status == status)
        return query.order_by(Dispute.created_at.desc()).offset(offset).limit(limit).all()

    def create_dispute(
        self,
        transaction_id: str,
        razorpay_dispute_id: str,
        dispute_amount: float,
        reason_code: str,
        respond_by: datetime,
        status: str = "OPEN"
    ) -> Dispute:
        dispute = Dispute(
            transaction_id=transaction_id,
            razorpay_dispute_id=razorpay_dispute_id,
            dispute_amount=dispute_amount,
            reason_code=reason_code,
            respond_by=respond_by,
            status=status
        )
        self.db.add(dispute)
        self.db.commit()
        self.db.refresh(dispute)
        return dispute

    def update_status(self, dispute_id: str, new_status: str) -> Optional[Dispute]:
        dispute = self.get_by_id(dispute_id)
        if dispute:
            dispute.status = new_status
            self.db.commit()
            self.db.refresh(dispute)
        return dispute


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log_event(
        self,
        actor_type: str,
        actor_id: str,
        action_taken: str,
        dispute_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        audit_entry = AuditLog(
            dispute_id=dispute_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action_taken=action_taken,
            payload=payload or {}
        )
        self.db.add(audit_entry)
        self.db.commit()
        self.db.refresh(audit_entry)
        logger.info(f"AUDIT LOG [{actor_type}:{actor_id}] -> {action_taken} (Dispute: {dispute_id})")
        return audit_entry

    def list_logs_for_dispute(self, dispute_id: str) -> List[AuditLog]:
        return self.db.query(AuditLog).filter(AuditLog.dispute_id == dispute_id).order_by(AuditLog.timestamp.asc()).all()


class WebhookRepository:
    def __init__(self, db: Session):
        self.db = db

    def is_duplicate(self, event_id: str) -> bool:
        """Checks if event_id has already been recorded in deduplication index."""
        return self.db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).first() is not None

    def record_event(self, event_id: str, event_type: str, payload: Dict[str, Any]) -> Optional[WebhookEvent]:
        if self.is_duplicate(event_id):
            logger.warning(f"Duplicate webhook event detected and rejected: {event_id}")
            return None

        event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            processed=False
        )
        try:
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            return event
        except IntegrityError:
            self.db.rollback()
            logger.warning(f"IntegrityError on duplicate event_id: {event_id}")
            return None
