from fastapi import APIRouter, Request, Header, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.db.session import get_db
from app.db.repositories import WebhookRepository, DisputeRepository, CustomerRepository
from app.services.razorpay_adapter import verify_razorpay_webhook_signature
from app.services.agent_service import AIAgentInvestigator
from app.db.models import Transaction, Dispute
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/razorpay", status_code=status.HTTP_200_OK)
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    body_bytes = await request.body()
    
    # 1. Signature Verification (Skip in local dev mock if signature header is mock)
    if x_razorpay_signature and x_razorpay_signature != "mock_signature_for_dev":
        is_valid = verify_razorpay_webhook_signature(
            payload_body=body_bytes,
            signature=x_razorpay_signature,
            secret=settings.RAZORPAY_WEBHOOK_SECRET
        )
        if not is_valid:
            logger.warning("Razorpay webhook signature verification failed.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Razorpay webhook signature")

    # 2. JSON Parsing
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    event_id = payload.get("event_id") or payload.get("id") or f"evt_mock_{hash(body_bytes)}"
    event_type = payload.get("event", "dispute.created")

    # 3. Deduplication Check via WebhookRepository
    webhook_repo = WebhookRepository(db)
    recorded_event = webhook_repo.record_event(
        event_id=str(event_id),
        event_type=event_type,
        payload=payload
    )

    if recorded_event is None:
        return {
            "status": "ignored_duplicate",
            "message": f"Webhook event {event_id} already processed.",
            "event_id": str(event_id)
        }

    # 4. Process Dispute Ingestion & Auto-Trigger AI Agent
    if event_type in ["dispute.created", "dispute.under_review"]:
        entity = payload.get("payload", {}).get("dispute", {}).get("entity", {})
        razorpay_dispute_id = entity.get("id", f"disp_wh_{event_id[:8]}")
        payment_id = entity.get("payment_id", f"pay_wh_{event_id[:8]}")
        amount_paise = entity.get("amount", 210000)
        dispute_amount = float(amount_paise) / 100.0
        reason_code = entity.get("reason_code", "merchandise_not_received")

        dispute_repo = DisputeRepository(db)
        existing_dispute = dispute_repo.get_by_razorpay_id(razorpay_dispute_id)

        if not existing_dispute:
            # Create dummy customer & transaction if needed
            cust_repo = CustomerRepository(db)
            customer = cust_repo.create(email=f"customer.wh.{event_id[:6]}@example.com")
            
            tx = Transaction(
                customer_id=customer.id,
                razorpay_payment_id=payment_id,
                amount=dispute_amount,
                currency="INR",
                payment_method="UPI",
                device_fingerprint="fp_wh_device",
                ip_country="IN"
            )
            db.add(tx)
            db.commit()

            dispute = dispute_repo.create_dispute(
                transaction_id=tx.id,
                razorpay_dispute_id=razorpay_dispute_id,
                dispute_amount=dispute_amount,
                reason_code=reason_code,
                respond_by=datetime.now(timezone.utc) + timedelta(days=7),
                status="OPEN"
            )

            # Auto-trigger AI Investigator
            investigator = AIAgentInvestigator(db)
            investigator.investigate(dispute.id)

    return {
        "status": "processed",
        "event_id": str(event_id),
        "event_type": event_type
    }
