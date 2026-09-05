import time
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.repositories import DisputeRepository, AuditRepository
from app.db.models import Dispute, AuditLog
from app.core.logging import logger

class PolicyOutcome(str, Enum):
    ALLOWED = "ALLOWED"
    REQUIRES_HUMAN_APPROVAL = "REQUIRES_HUMAN_APPROVAL"
    BLOCKED = "BLOCKED"

class ActionType(str, Enum):
    DEFEND = "DEFEND"
    ACCEPT = "ACCEPT"
    ESCALATE_FOR_REVIEW = "ESCALATE_FOR_REVIEW"

class ActorType(str, Enum):
    SYSTEM = "SYSTEM"
    AI_AGENT = "AI_AGENT"
    HUMAN_USER = "HUMAN_USER"

class ActionRequest(BaseModel):
    dispute_id: str
    action: ActionType
    actor_type: ActorType
    actor_id: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    dispute_amount: float = Field(..., ge=0.0)
    ai_confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    supporting_evidence: List[str] = Field(default_factory=list)

class PolicyEvaluationResult(BaseModel):
    outcome: PolicyOutcome
    reason: str
    rule_triggered: str

class ActionResponse(BaseModel):
    dispute_id: str
    action_requested: ActionType
    outcome: PolicyOutcome
    executed: bool
    new_status: str
    reason: str
    rule_triggered: str
    executed_at: str

class PolicyEngine:
    AUTO_EXECUTION_AMOUNT_CEILING = 5000.0  # Disputes > ₹5,000 require human review
    MIN_CONFIDENCE_THRESHOLD = 0.85          # Confidence < 85% requires human review
    HIGH_RISK_THRESHOLD = 0.70               # Risk score >= 0.70 is High Risk

    def __init__(self, db: Session):
        self.db = db
        self.dispute_repo = DisputeRepository(db)
        self.audit_repo = AuditRepository(db)

    def evaluate_policy(self, req: ActionRequest) -> PolicyEvaluationResult:
        dispute = self.dispute_repo.get_by_id(req.dispute_id)
        if not dispute:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.BLOCKED,
                reason=f"Dispute {req.dispute_id} not found in database.",
                rule_triggered="P0_NOT_FOUND"
            )

        # Rule P1: State Machine Idempotency (Cannot act on finalized dispute)
        if dispute.status in ["DEFENDED", "ACCEPTED"]:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.BLOCKED,
                reason=f"Dispute {req.dispute_id} is already in a finalized state ({dispute.status}). Action rejected.",
                rule_triggered="P1_STATE_FINALIZED_IDEMPOTENCY"
            )

        # Rule P5: Missing Evidence Guard for DEFEND action
        if req.action == ActionType.DEFEND and len(req.supporting_evidence) == 0:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.BLOCKED,
                reason="Cannot submit chargeback defense without verified supporting evidence.",
                rule_triggered="P5_MISSING_EVIDENCE_GUARD"
            )

        # Rule P4: Conflict / Policy Ceiling Guard (Auto-accepting high-risk disputes)
        if req.action == ActionType.ACCEPT and req.risk_score >= self.HIGH_RISK_THRESHOLD and req.actor_type != ActorType.HUMAN_USER:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.BLOCKED,
                reason=f"Automated acceptance of high-risk dispute ({req.risk_score:.0%}) is prohibited by risk policy.",
                rule_triggered="P4_HIGH_RISK_AUTO_ACCEPT_PROHIBITED"
            )

        # Rule P6: Human Authorized explicit action (Human override)
        if req.actor_type == ActorType.HUMAN_USER:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.ALLOWED,
                reason=f"Action explicitly authorized by Human User ({req.actor_id}).",
                rule_triggered="P6_HUMAN_EXPLICIT_AUTHORIZATION"
            )

        # Rule P7: High Risk Automated Escalation (High Risk >= 0.70 requires human approval)
        if req.risk_score >= self.HIGH_RISK_THRESHOLD and req.actor_type != ActorType.HUMAN_USER and req.action != ActionType.ESCALATE_FOR_REVIEW:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.REQUIRES_HUMAN_APPROVAL,
                reason=f"High risk dispute ({req.risk_score:.0%}) requires mandatory human compliance approval.",
                rule_triggered="P7_HIGH_RISK_HUMAN_REVIEW_REQUIRED"
            )

        # Rule P2: Financial Ceiling Guard for automated actions
        if req.dispute_amount > self.AUTO_EXECUTION_AMOUNT_CEILING:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.REQUIRES_HUMAN_APPROVAL,
                reason=f"Dispute amount (INR {req.dispute_amount:,.2f}) exceeds automated ceiling of INR {self.AUTO_EXECUTION_AMOUNT_CEILING:,.2f}. Mandatory human review required.",
                rule_triggered="P2_FINANCIAL_AMOUNT_CEILING"
            )

        # Rule P3: Low Confidence Escalation
        if req.ai_confidence < self.MIN_CONFIDENCE_THRESHOLD:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.REQUIRES_HUMAN_APPROVAL,
                reason=f"AI recommendation confidence ({req.ai_confidence:.0%}) is below safety threshold ({self.MIN_CONFIDENCE_THRESHOLD:.0%}).",
                rule_triggered="P3_LOW_CONFIDENCE_ESCALATION"
            )

        # Default: ALLOWED for safe, low-risk, verified automated actions
        return PolicyEvaluationResult(
            outcome=PolicyOutcome.ALLOWED,
            reason="Action meets all automated safety criteria and policy guardrails.",
            rule_triggered="P0_AUTOMATED_POLICY_PASSED"
        )

    def execute_action(self, req: ActionRequest) -> ActionResponse:
        eval_result = self.evaluate_policy(req)
        dispute = self.dispute_repo.get_by_id(req.dispute_id)
        current_status = dispute.status if dispute else "UNKNOWN"
        new_status = current_status
        executed = False

        if eval_result.outcome == PolicyOutcome.ALLOWED:
            if req.action == ActionType.DEFEND:
                new_status = "DEFENDED"
            elif req.action == ActionType.ACCEPT:
                new_status = "ACCEPTED"
            elif req.action == ActionType.ESCALATE_FOR_REVIEW:
                new_status = "UNDER_REVIEW"

            self.dispute_repo.update_status(req.dispute_id, new_status)
            executed = True

            self.audit_repo.log_event(
                actor_type=req.actor_type.value,
                actor_id=req.actor_id,
                action_taken=f"ACTION_EXECUTED_{req.action.value}",
                dispute_id=req.dispute_id,
                payload={
                    "outcome": eval_result.outcome.value,
                    "previous_status": current_status,
                    "new_status": new_status,
                    "rule_triggered": eval_result.rule_triggered,
                    "reason": eval_result.reason
                }
            )

        elif eval_result.outcome == PolicyOutcome.REQUIRES_HUMAN_APPROVAL:
            new_status = "UNDER_REVIEW"
            self.dispute_repo.update_status(req.dispute_id, new_status)
            executed = False

            self.audit_repo.log_event(
                actor_type=req.actor_type.value,
                actor_id=req.actor_id,
                action_taken="ESCALATED_HUMAN_APPROVAL_REQUIRED",
                dispute_id=req.dispute_id,
                payload={
                    "requested_action": req.action.value,
                    "previous_status": current_status,
                    "new_status": new_status,
                    "rule_triggered": eval_result.rule_triggered,
                    "reason": eval_result.reason
                }
            )

        elif eval_result.outcome == PolicyOutcome.BLOCKED:
            executed = False
            self.audit_repo.log_event(
                actor_type=req.actor_type.value,
                actor_id=req.actor_id,
                action_taken="ACTION_BLOCKED_POLICY_VIOLATION",
                dispute_id=req.dispute_id,
                payload={
                    "requested_action": req.action.value,
                    "current_status": current_status,
                    "rule_triggered": eval_result.rule_triggered,
                    "reason": eval_result.reason
                }
            )

        return ActionResponse(
            dispute_id=req.dispute_id,
            action_requested=req.action,
            outcome=eval_result.outcome,
            executed=executed,
            new_status=new_status,
            reason=eval_result.reason,
            rule_triggered=eval_result.rule_triggered,
            executed_at=datetime.now(timezone.utc).isoformat()
        )
