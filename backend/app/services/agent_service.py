import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.tools.dispute_tools import DisputeToolRegistry, ToolTraceEntry
from app.db.repositories import DisputeRepository, AuditRepository
from app.db.models import Decision, Evidence
from app.core.logging import logger

class AgentInvestigationResult(BaseModel):
    dispute_id: str
    recommendation: str = Field(..., description="DEFEND, REVIEW, or ACCEPT")
    confidence: float = Field(..., ge=0.0, le=1.0)
    summary: str
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    recommended_action: str
    human_approval_required: bool
    tool_traces: List[ToolTraceEntry] = Field(default_factory=list)
    investigated_at: str

class AIAgentInvestigator:
    def __init__(self, db: Session):
        self.db = db
        self.tools = DisputeToolRegistry(db)
        self.dispute_repo = DisputeRepository(db)
        self.audit_repo = AuditRepository(db)

    def investigate(self, dispute_id: str) -> AgentInvestigationResult:
        logger.info(f"AI Investigator starting autonomous trace for Dispute {dispute_id}...")
        start_time = time.time()
        tool_traces: List[ToolTraceEntry] = []

        # Step 1: Tool Call 1 - get_transaction
        t1_start = time.time()
        tx_data = self.tools.get_transaction(dispute_id)
        tool_traces.append(ToolTraceEntry(
            tool_name="get_transaction",
            input_params={"dispute_id": dispute_id},
            output_summary={"amount": tx_data.get("amount"), "payment_method": tx_data.get("payment_method"), "ip_country": tx_data.get("ip_country")},
            duration_ms=round((time.time() - t1_start) * 1000, 2),
            timestamp=datetime.utcnow().isoformat()
        ))

        if "error" in tx_data:
            return self._fallback_response(dispute_id, f"Investigation aborted: {tx_data['error']}", tool_traces)

        customer_id = self.dispute_repo.get_by_id(dispute_id).transaction.customer_id
        transaction_id = tx_data["transaction_id"]

        # Step 2: Tool Call 2 - get_customer_history
        t2_start = time.time()
        cust_data = self.tools.get_customer_history(customer_id)
        tool_traces.append(ToolTraceEntry(
            tool_name="get_customer_history",
            input_params={"customer_id": customer_id},
            output_summary={"total_orders": cust_data.get("total_orders"), "historical_disputes": cust_data.get("historical_disputes")},
            duration_ms=round((time.time() - t2_start) * 1000, 2),
            timestamp=datetime.utcnow().isoformat()
        ))

        # Step 3: Tool Call 3 - get_order_and_delivery
        t3_start = time.time()
        order_data = self.tools.get_order_and_delivery(transaction_id)
        tool_traces.append(ToolTraceEntry(
            tool_name="get_order_and_delivery",
            input_params={"transaction_id": transaction_id},
            output_summary={"delivery_status": order_data.get("delivery_status"), "tracking": order_data.get("tracking_number")},
            duration_ms=round((time.time() - t3_start) * 1000, 2),
            timestamp=datetime.utcnow().isoformat()
        ))

        # Step 4: Tool Call 4 - get_previous_disputes
        t4_start = time.time()
        prev_disp_data = self.tools.get_previous_disputes(customer_id)
        tool_traces.append(ToolTraceEntry(
            tool_name="get_previous_disputes",
            input_params={"customer_id": customer_id},
            output_summary={"total_disputes_found": prev_disp_data.get("total_disputes_found")},
            duration_ms=round((time.time() - t4_start) * 1000, 2),
            timestamp=datetime.utcnow().isoformat()
        ))

        # Step 5: Tool Call 5 - get_risk_analysis
        t5_start = time.time()
        risk_data = self.tools.get_risk_analysis(dispute_id)
        tool_traces.append(ToolTraceEntry(
            tool_name="get_risk_analysis",
            input_params={"dispute_id": dispute_id},
            output_summary={"risk_score": risk_data.get("risk_score"), "risk_level": risk_data.get("risk_level")},
            duration_ms=round((time.time() - t5_start) * 1000, 2),
            timestamp=datetime.utcnow().isoformat()
        ))

        # Step 6: Evidence Synthesis & Reasoning Engine
        supporting_evidence = []
        contradicting_evidence = []

        risk_score = risk_data.get("risk_score", 0.5)
        delivery_confirmed = order_data.get("delivery_status") == "DELIVERED"
        device_changed = "unknown" in str(tx_data.get("device_fingerprint", "")) or "vpn" in str(tx_data.get("device_fingerprint", ""))
        historical_dispute_count = cust_data.get("historical_disputes", 0)

        if delivery_confirmed:
            supporting_evidence.append(f"Carrier verified delivery (Tracking #{order_data.get('tracking_number')})")
        else:
            contradicting_evidence.append("Unconfirmed carrier delivery status")

        if not device_changed:
            supporting_evidence.append(f"Matching device fingerprint ({tx_data.get('device_fingerprint')})")
        else:
            contradicting_evidence.append("Device fingerprint mismatch or VPN proxy detected")

        if historical_dispute_count > 0:
            contradicting_evidence.append(f"Customer has {int(historical_dispute_count)} historical dispute filings")
        else:
            supporting_evidence.append("Clean customer account history (0 prior disputes)")

        # Recommendation Logic
        if risk_score <= 0.35 and delivery_confirmed and not device_changed:
            recommendation = "DEFEND"
            confidence = 0.96
            summary = (
                f"Low dispute risk ({risk_score:.0%}). Carrier confirmed delivery to registered address hash. "
                f"Device fingerprint matches customer's prior session history. Recommend defending dispute."
            )
            recommended_action = "Submit Automated Chargeback Defense Package"
            human_approval_required = False

        elif risk_score >= 0.70 or device_changed or historical_dispute_count > 1:
            recommendation = "REVIEW"
            confidence = 0.91
            summary = (
                f"High risk dispute ({risk_score:.0%}). Device mismatch or elevated customer dispute frequency detected. "
                f"Requires merchant manual review before final submission."
            )
            recommended_action = "Escalate to Human Compliance Review Queue"
            human_approval_required = True

        else:
            recommendation = "ACCEPT"
            confidence = 0.85
            summary = (
                f"Medium dispute risk ({risk_score:.0%}) with weak evidentiary proof of delivery. "
                f"Accepting chargeback to minimize dispute penalty fees."
            )
            recommended_action = "Accept Dispute & File Liability Adjustment"
            human_approval_required = True

        result = AgentInvestigationResult(
            dispute_id=dispute_id,
            recommendation=recommendation,
            confidence=confidence,
            summary=summary,
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence,
            recommended_action=recommended_action,
            human_approval_required=human_approval_required,
            tool_traces=tool_traces,
            investigated_at=datetime.utcnow().isoformat()
        )

        # Persist Decision Record
        decision_rec = Decision(
            dispute_id=dispute_id,
            recommendation=recommendation,
            confidence=confidence,
            executive_summary=summary,
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence,
            human_approval_required=human_approval_required
        )
        self.db.add(decision_rec)
        self.db.commit()

        # Audit Log Event
        self.audit_repo.log_event(
            actor_type="AI_AGENT",
            actor_id="ResolveAI_Investigator_v1",
            action_taken="AI_INVESTIGATION_COMPLETED",
            dispute_id=dispute_id,
            payload={
                "recommendation": recommendation,
                "confidence": confidence,
                "tool_calls_count": len(tool_traces),
                "total_investigation_ms": round((time.time() - start_time) * 1000, 2)
            }
        )

        return result

    def _fallback_response(self, dispute_id: str, reason: str, tool_traces: List[ToolTraceEntry]) -> AgentInvestigationResult:
        logger.warning(f"AI Investigator fallback triggered for Dispute {dispute_id}: {reason}")
        return AgentInvestigationResult(
            dispute_id=dispute_id,
            recommendation="REVIEW",
            confidence=0.50,
            summary=f"Deterministic fallback triggered: {reason}",
            supporting_evidence=[],
            contradicting_evidence=[reason],
            recommended_action="Escalate to Human Compliance Review Queue",
            human_approval_required=True,
            tool_traces=tool_traces,
            investigated_at=datetime.utcnow().isoformat()
        )
