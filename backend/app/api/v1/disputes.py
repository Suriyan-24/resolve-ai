from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories import DisputeRepository, AuditRepository
from app.db.models import Dispute, RiskScore, Decision, Evidence
from app.services.agent_service import AIAgentInvestigator, AgentInvestigationResult
from app.ml.risk_engine import MLRiskEngine

router = APIRouter(prefix="/disputes", tags=["Disputes"])

@router.get("", status_code=status.HTTP_200_OK)
def list_disputes(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    repo = DisputeRepository(db)
    disputes = repo.list_disputes(status=status_filter, limit=limit, offset=offset)
    
    result = []
    for d in disputes:
        latest_risk = d.risk_scores[-1] if d.risk_scores else None
        latest_decision = d.decisions[-1] if d.decisions else None
        tx = d.transaction

        result.append({
            "id": d.id,
            "razorpay_dispute_id": d.razorpay_dispute_id,
            "dispute_amount": d.dispute_amount,
            "status": d.status,
            "reason_code": d.reason_code,
            "respond_by": str(d.respond_by),
            "created_at": str(d.created_at),
            "customer_email": tx.customer.email if (tx and tx.customer) else "unknown@example.com",
            "payment_method": tx.payment_method if tx else "UNKNOWN",
            "risk_score": latest_risk.risk_score if latest_risk else 0.50,
            "risk_level": latest_risk.risk_level if latest_risk else "MEDIUM",
            "recommendation": latest_decision.recommendation if latest_decision else "PENDING"
        })
    return result


@router.get("/metrics/summary", status_code=status.HTTP_200_OK)
def get_metrics_summary(db: Session = Depends(get_db)):
    disputes = db.query(Dispute).all()
    total_count = len(disputes)
    high_risk_count = 0
    under_review_count = 0
    protected_funds = 0.0

    for d in disputes:
        if d.status in ["UNDER_REVIEW", "OPEN"]:
            under_review_count += 1
        if d.status == "DEFENDED":
            protected_funds += d.dispute_amount
        if d.risk_scores and d.risk_scores[-1].risk_level == "HIGH":
            high_risk_count += 1

    return {
        "total_disputes": total_count,
        "high_risk_count": high_risk_count,
        "under_review_count": under_review_count,
        "protected_funds_inr": protected_funds
    }


@router.get("/{dispute_id}", status_code=status.HTTP_200_OK)
def get_dispute_detail(dispute_id: str, db: Session = Depends(get_db)):
    repo = DisputeRepository(db)
    dispute = repo.get_by_id(dispute_id)
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dispute {dispute_id} not found")

    tx = dispute.transaction
    cust = tx.customer if tx else None
    order = tx.order if tx else None
    latest_risk = dispute.risk_scores[-1] if dispute.risk_scores else None
    latest_decision = dispute.decisions[-1] if dispute.decisions else None

    # Gather evidence items
    evidence_list = []
    for ev in dispute.evidence:
        evidence_list.append({
            "id": ev.id,
            "evidence_type": ev.evidence_type,
            "metadata": ev.evidence_metadata,
            "verified": ev.verified,
            "assembled_at": str(ev.assembled_at)
        })

    return {
        "id": dispute.id,
        "razorpay_dispute_id": dispute.razorpay_dispute_id,
        "status": dispute.status,
        "dispute_amount": dispute.dispute_amount,
        "reason_code": dispute.reason_code,
        "respond_by": str(dispute.respond_by),
        "created_at": str(dispute.created_at),
        "transaction": {
            "id": tx.id if tx else None,
            "razorpay_payment_id": tx.razorpay_payment_id if tx else None,
            "amount": tx.amount if tx else 0.0,
            "payment_method": tx.payment_method if tx else None,
            "device_fingerprint": tx.device_fingerprint if tx else None,
            "ip_country": tx.ip_country if tx else None,
            "created_at": str(tx.created_at) if tx else None
        },
        "customer": {
            "id": cust.id if cust else None,
            "email": cust.email if cust else None,
            "total_orders": float(cust.total_orders) if cust else 0,
            "historical_disputes": float(cust.historical_disputes) if cust else 0
        },
        "order": {
            "id": order.id if order else None,
            "delivery_status": order.delivery_status if order else None,
            "tracking_number": order.tracking_number if order else None,
            "carrier_delivered_at": str(order.carrier_delivered_at) if (order and order.carrier_delivered_at) else None
        },
        "risk_score": {
            "score": latest_risk.risk_score if latest_risk else 0.50,
            "level": latest_risk.risk_level if latest_risk else "MEDIUM",
            "feature_contributions": latest_risk.feature_contributions if latest_risk else {}
        },
        "decision": {
            "recommendation": latest_decision.recommendation if latest_decision else "PENDING",
            "confidence": latest_decision.confidence if latest_decision else 0.0,
            "executive_summary": latest_decision.executive_summary if latest_decision else "Pending AI Investigation",
            "supporting_evidence": latest_decision.supporting_evidence if latest_decision else [],
            "contradicting_evidence": latest_decision.contradicting_evidence if latest_decision else [],
            "human_approval_required": latest_decision.human_approval_required if latest_decision else True
        },
        "evidence": evidence_list
    }


@router.post("/{dispute_id}/investigate", status_code=status.HTTP_200_OK)
def trigger_investigation(dispute_id: str, db: Session = Depends(get_db)):
    repo = DisputeRepository(db)
    dispute = repo.get_by_id(dispute_id)
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dispute {dispute_id} not found")

    investigator = AIAgentInvestigator(db)
    result = investigator.investigate(dispute_id)
    return result


@router.get("/{dispute_id}/trace", status_code=status.HTTP_200_OK)
def get_investigation_trace(dispute_id: str, db: Session = Depends(get_db)):
    repo = DisputeRepository(db)
    dispute = repo.get_by_id(dispute_id)
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dispute {dispute_id} not found")

    investigator = AIAgentInvestigator(db)
    result = investigator.investigate(dispute_id)
    return {
        "dispute_id": dispute_id,
        "tool_traces": result.tool_traces
    }
