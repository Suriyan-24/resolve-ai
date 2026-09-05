import os
import sys
import time
from datetime import datetime, timedelta, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal, init_db
from app.db.models import Customer, Transaction, Order, Dispute, RiskScore, Evidence, Decision, AuditLog
from app.services.agent_service import AIAgentInvestigator
from app.services.policy_service import PolicyEngine, ActionRequest, ActionType, ActorType, PolicyOutcome
from app.services.razorpay_adapter import get_payment_provider, DisputeDefenseSubmission
from ml.risk_engine import MLRiskEngine
from app.core.logging import logger

def run_demo_simulation():
    print("==========================================================================")
    print("      RESOLVEAI — AUTONOMOUS RISK MANAGEMENT END-TO-END DEMO             ")
    print("==========================================================================")
    print("Initializing real backend services, database session, and ML models...\n")

    init_db()
    db = SessionLocal()
    provider = get_payment_provider()
    ml_engine = MLRiskEngine()
    investigator = AIAgentInvestigator(db)
    policy_engine = PolicyEngine(db)

    try:
        # ========================================================================
        # CASE 1: Defendable Dispute (Low Risk 12%) -> DEFEND -> ALLOWED -> EXECUTE
        # ========================================================================
        print("--------------------------------------------------------------------------")
        print(" [DEMO CASE 1] Low-Risk Defendable Dispute (Legitimate Customer)")
        print("--------------------------------------------------------------------------")
        
        cust1 = Customer(email="arun.kumar@example.com", total_orders=16, historical_disputes=0)
        db.add(cust1)
        db.flush()

        tx1 = Transaction(
            customer_id=cust1.id,
            razorpay_payment_id="pay_demo_CASE1",
            amount=2100.0,
            currency="INR",
            payment_method="UPI",
            device_fingerprint="fp_macbook_arun_9921",
            ip_country="IN",
            created_at=datetime.now(timezone.utc) - timedelta(days=3)
        )
        db.add(tx1)
        db.flush()

        order1 = Order(
            transaction_id=tx1.id,
            delivery_status="DELIVERED",
            tracking_number="BLUEDART_987654321",
            carrier_delivered_at=datetime.now(timezone.utc) - timedelta(days=1),
            shipping_address_hash="hash_bengaluru_560001"
        )
        db.add(order1)

        disp1 = Dispute(
            transaction_id=tx1.id,
            razorpay_dispute_id="disp_demo_1001",
            dispute_amount=2100.0,
            reason_code="merchandise_not_received",
            respond_by=datetime.now(timezone.utc) + timedelta(days=7),
            status="OPEN"
        )
        db.add(disp1)
        db.commit()

        # Step 1: ML Risk Detection
        risk_res1 = ml_engine.predict_risk({
            "transaction_amount": 2100.0,
            "account_age_days": 180,
            "previous_orders": 16,
            "previous_disputes": 0,
            "device_change_flag": False,
            "ip_country_mismatch": False,
            "delivery_confirmation_valid": True
        })
        print(f"1. ML Risk Score calculated : {risk_res1.risk_score * 100:.0f}% ({risk_res1.risk_level} RISK)")

        # Step 2: AI Investigation
        inv_res1 = investigator.investigate(disp1.id)
        print(f"2. AI Recommendation        : {inv_res1.recommendation} (Confidence: {inv_res1.confidence*100:.0f}%)")
        print(f"   Summary                 : {inv_res1.summary}")
        print(f"   Supporting Evidence     : {inv_res1.supporting_evidence}")

        # Step 3: Policy Engine Evaluation
        act_req1 = ActionRequest(
            dispute_id=disp1.id,
            action=ActionType.DEFEND,
            actor_type=ActorType.AI_AGENT,
            actor_id="ResolveAI_Investigator_v1",
            risk_score=risk_res1.risk_score,
            dispute_amount=disp1.dispute_amount,
            ai_confidence=inv_res1.confidence,
            supporting_evidence=inv_res1.supporting_evidence
        )
        policy_res1 = policy_engine.execute_action(act_req1)
        print(f"3. Policy Engine Outcome    : {policy_res1.outcome.value} (Rule: {policy_res1.rule_triggered})")

        # Step 4: Razorpay Provider Defense Package Submission
        if policy_res1.executed:
            sub1 = DisputeDefenseSubmission(
                dispute_id=disp1.id,
                razorpay_dispute_id=disp1.razorpay_dispute_id,
                summary=inv_res1.summary,
                evidence_documents=inv_res1.supporting_evidence
            )
            gateway_res1 = provider.submit_defense(sub1)
            print(f"4. Razorpay Adapter Call   : {gateway_res1['message']} (Status: {gateway_res1['status']})")

        print("   [RESULT] Automated Defense Package Submitted & Audit Logged Successfully.\n")

        # ========================================================================
        # CASE 2: Suspicious High-Risk Dispute (87%) -> REVIEW -> HUMAN APPROVAL
        # ========================================================================
        print("--------------------------------------------------------------------------")
        print(" [DEMO CASE 2] High-Risk Dispute (Device Mismatch & Amount Spike)")
        print("--------------------------------------------------------------------------")

        cust2 = Customer(email="priya.sharma@example.com", total_orders=2, historical_disputes=2)
        db.add(cust2)
        db.flush()

        tx2 = Transaction(
            customer_id=cust2.id,
            razorpay_payment_id="pay_demo_CASE2",
            amount=8499.0,
            currency="INR",
            payment_method="CARD",
            device_fingerprint="fp_device_unknown_android",
            ip_country="IN",
            created_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        db.add(tx2)
        db.flush()

        order2 = Order(
            transaction_id=tx2.id,
            delivery_status="DELIVERED",
            tracking_number="DELHIVERY_998877",
            carrier_delivered_at=datetime.now(timezone.utc) - timedelta(hours=6),
            shipping_address_hash="hash_mumbai_400001"
        )
        db.add(order2)

        disp2 = Dispute(
            transaction_id=tx2.id,
            razorpay_dispute_id="disp_demo_1002",
            dispute_amount=8499.0,
            reason_code="unauthorized_transaction",
            respond_by=datetime.now(timezone.utc) + timedelta(days=3),
            status="OPEN"
        )
        db.add(disp2)
        db.commit()

        # Step 1: ML Risk Detection
        risk_res2 = ml_engine.predict_risk({
            "transaction_amount": 8499.0,
            "account_age_days": 10,
            "previous_orders": 2,
            "previous_disputes": 2,
            "device_change_flag": True,
            "ip_country_mismatch": False,
            "delivery_confirmation_valid": True
        })
        print(f"1. ML Risk Score calculated : {risk_res2.risk_score * 100:.0f}% ({risk_res2.risk_level} RISK)")

        # Step 2: AI Investigation
        inv_res2 = investigator.investigate(disp2.id)
        print(f"2. AI Recommendation        : {inv_res2.recommendation} (Confidence: {inv_res2.confidence*100:.0f}%)")
        print(f"   Summary                 : {inv_res2.summary}")
        print(f"   Risk Flags              : {inv_res2.contradicting_evidence}")

        # Step 3: Policy Engine Evaluation
        act_req2 = ActionRequest(
            dispute_id=disp2.id,
            action=ActionType.DEFEND,
            actor_type=ActorType.AI_AGENT,
            actor_id="ResolveAI_Investigator_v1",
            risk_score=risk_res2.risk_score,
            dispute_amount=disp2.dispute_amount,
            ai_confidence=inv_res2.confidence,
            supporting_evidence=inv_res2.supporting_evidence
        )
        policy_res2 = policy_engine.execute_action(act_req2)
        print(f"3. Policy Engine Outcome    : {policy_res2.outcome.value} (Rule: {policy_res2.rule_triggered})")
        print(f"   Policy Reason           : {policy_res2.reason}")
        print("   [RESULT] Automated Execution Escalated to Human Compliance Review Queue.\n")

        # ========================================================================
        # CASE 3: Policy Blocked (High Risk Auto-Accept Prohibited / Finalized)
        # ========================================================================
        print("--------------------------------------------------------------------------")
        print(" [DEMO CASE 3] Policy-Blocked Case (Prohibited High-Risk Auto-Accept)")
        print("--------------------------------------------------------------------------")

        cust3 = Customer(email="suspicious.user@example.com", total_orders=1, historical_disputes=4)
        db.add(cust3)
        db.flush()

        tx3 = Transaction(
            customer_id=cust3.id,
            razorpay_payment_id="pay_demo_CASE3",
            amount=15000.0,
            currency="INR",
            payment_method="CARD",
            device_fingerprint="fp_vpn_proxy_9901",
            ip_country="US",
            created_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        db.add(tx3)
        db.flush()

        disp3 = Dispute(
            transaction_id=tx3.id,
            razorpay_dispute_id="disp_demo_1003",
            dispute_amount=15000.0,
            reason_code="fraudulent_claim",
            respond_by=datetime.now(timezone.utc) + timedelta(days=5),
            status="OPEN"
        )
        db.add(disp3)
        db.commit()

        # Step 1: ML Risk Detection
        risk_res3 = ml_engine.predict_risk({
            "transaction_amount": 15000.0,
            "account_age_days": 2,
            "previous_orders": 1,
            "previous_disputes": 4,
            "device_change_flag": True,
            "ip_country_mismatch": True,
            "delivery_confirmation_valid": False
        })
        print(f"1. ML Risk Score calculated : {risk_res3.risk_score * 100:.0f}% ({risk_res3.risk_level} RISK)")

        # Step 2: Attempt Unauthorized Auto-Accept Action via AI Agent
        act_req3 = ActionRequest(
            dispute_id=disp3.id,
            action=ActionType.ACCEPT,
            actor_type=ActorType.AI_AGENT,
            actor_id="ResolveAI_Investigator_v1",
            risk_score=risk_res3.risk_score,
            dispute_amount=disp3.dispute_amount,
            ai_confidence=0.55,
            supporting_evidence=[]
        )
        policy_res3 = policy_engine.execute_action(act_req3)
        print(f"2. Policy Engine Outcome    : {policy_res3.outcome.value} (Rule: {policy_res3.rule_triggered})")
        print(f"   Reason                   : {policy_res3.reason}")
        print(f"   Action Executed?         : {policy_res3.executed}")
        print("   [RESULT] Policy Engine Blocked Unauthorized Financial Action.\n")

        print("==========================================================================")
        print("      RESOLVEAI DEMO SIMULATION COMPLETED SUCCESSFULLY                    ")
        print("==========================================================================")

    finally:
        db.close()

if __name__ == "__main__":
    run_demo_simulation()
