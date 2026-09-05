import os
import sys
from datetime import datetime, timedelta

# Ensure backend directory is in pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal, init_db
from app.db.models import (
    Customer, Transaction, Order, Dispute, 
    RiskScore, Evidence, Decision, AuditLog
)
from app.core.logging import logger

def seed_database():
    logger.info("Initializing database schema...")
    init_db()

    db = SessionLocal()
    try:
        # Clear existing data
        db.query(AuditLog).delete()
        db.query(Decision).delete()
        db.query(Evidence).delete()
        db.query(RiskScore).delete()
        db.query(Dispute).delete()
        db.query(Order).delete()
        db.query(Transaction).delete()
        db.query(Customer).delete()
        db.commit()

        logger.info("Seeding Demo Scenarios...")

        # ----------------------------------------------------
        # SCENARIO A: Dispute #1024 (Clear Fraud Defense - Low Risk 12%)
        # ----------------------------------------------------
        cust1 = Customer(
            email="arun.kumar@example.com",
            total_orders=16,
            historical_disputes=0
        )
        db.add(cust1)
        db.flush()

        tx1 = Transaction(
            customer_id=cust1.id,
            razorpay_payment_id="pay_K1024_DEFEND",
            amount=2100.0,
            currency="INR",
            payment_method="UPI",
            device_fingerprint="fp_device_arun_macbook_9921",
            ip_country="IN",
            created_at=datetime.utcnow() - timedelta(days=5)
        )
        db.add(tx1)
        db.flush()

        order1 = Order(
            transaction_id=tx1.id,
            delivery_status="DELIVERED",
            tracking_number="BLUEDART_987654321",
            carrier_delivered_at=datetime.utcnow() - timedelta(days=3),
            shipping_address_hash="hash_bengaluru_560001"
        )
        db.add(order1)

        disp1 = Dispute(
            transaction_id=tx1.id,
            razorpay_dispute_id="disp_1024",
            status="DEFENDED",
            dispute_amount=2100.0,
            reason_code="merchandise_not_received",
            respond_by=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        db.add(disp1)
        db.flush()

        risk1 = RiskScore(
            dispute_id=disp1.id,
            risk_score=0.12,
            risk_level="LOW",
            feature_contributions={"device_match": -0.45, "carrier_delivered": -0.30, "past_disputes": 0.0}
        )
        db.add(risk1)

        ev1_1 = Evidence(
            dispute_id=disp1.id,
            evidence_type="delivery_confirmation",
            evidence_metadata={"carrier": "BlueDart", "delivered_at": str(order1.carrier_delivered_at), "signed_by": "A. Kumar"},
            verified=True
        )
        ev1_2 = Evidence(
            dispute_id=disp1.id,
            evidence_type="device_fingerprint_match",
            evidence_metadata={"fingerprint": tx1.device_fingerprint, "prior_sessions": 16},
            verified=True
        )
        db.add_all([ev1_1, ev1_2])

        dec1 = Decision(
            dispute_id=disp1.id,
            recommendation="DEFEND",
            confidence=0.96,
            executive_summary="Carrier confirmation confirms delivery to registered address. Device fingerprint matches 16 previous legitimate transactions. Strong defense evidence assembled.",
            supporting_evidence=["Carrier Proof of Delivery", "Matching Device Fingerprint", "Clean Customer History"],
            contradicting_evidence=[],
            human_approval_required=False
        )
        db.add(dec1)

        log1 = AuditLog(
            dispute_id=disp1.id,
            actor_type="AI_AGENT",
            actor_id="ResolveAI_Investigator_v1",
            action_taken="AUTOMATED_DEFENSE_SUBMITTED",
            payload={"dispute_id": "disp_1024", "recommendation": "DEFEND", "policy_state": "ALLOWED"}
        )
        db.add(log1)

        # ----------------------------------------------------
        # SCENARIO B: Dispute #1023 (Friendly Fraud / Review Required - High Risk 87%)
        # ----------------------------------------------------
        cust2 = Customer(
            email="priya.sharma@example.com",
            total_orders=3,
            historical_disputes=2
        )
        db.add(cust2)
        db.flush()

        tx2 = Transaction(
            customer_id=cust2.id,
            razorpay_payment_id="pay_K1023_REVIEW",
            amount=8499.0,
            currency="INR",
            payment_method="CARD",
            device_fingerprint="fp_device_unknown_android_77",
            ip_country="IN",
            created_at=datetime.utcnow() - timedelta(days=2)
        )
        db.add(tx2)
        db.flush()

        order2 = Order(
            transaction_id=tx2.id,
            delivery_status="DELIVERED",
            tracking_number="DELHIVERY_11223344",
            carrier_delivered_at=datetime.utcnow() - timedelta(days=1),
            shipping_address_hash="hash_mumbai_400001"
        )
        db.add(order2)

        disp2 = Dispute(
            transaction_id=tx2.id,
            razorpay_dispute_id="disp_1023",
            status="UNDER_REVIEW",
            dispute_amount=8499.0,
            reason_code="unauthorized_transaction",
            respond_by=datetime.utcnow() + timedelta(days=3),
            created_at=datetime.utcnow() - timedelta(hours=6)
        )
        db.add(disp2)
        db.flush()

        risk2 = RiskScore(
            dispute_id=disp2.id,
            risk_score=0.87,
            risk_level="HIGH",
            feature_contributions={"device_mismatch": 0.40, "amount_spike": 0.35, "past_disputes": 0.25}
        )
        db.add(risk2)

        ev2_1 = Evidence(
            dispute_id=disp2.id,
            evidence_type="device_fingerprint_mismatch",
            evidence_metadata={"device": tx2.device_fingerprint, "registered_device": "fp_device_priya_iphone_12"},
            verified=True
        )
        ev2_2 = Evidence(
            dispute_id=disp2.id,
            evidence_type="customer_history",
            evidence_metadata={"past_disputes": 2, "avg_order_value": 1800.0, "current_order": 8499.0},
            verified=True
        )
        db.add_all([ev2_1, ev2_2])

        dec2 = Decision(
            dispute_id=disp2.id,
            recommendation="REVIEW",
            confidence=0.91,
            executive_summary="Dispute amount ₹8,499 is 4.7x customer historical average. Device fingerprint changed 2 days prior to order and customer has 2 past dispute filings. Escalated for human review.",
            supporting_evidence=["Device Mismatch Detected", "High Transaction Value Spike"],
            contradicting_evidence=["Carrier Delivery Timestamp Valid"],
            human_approval_required=True
        )
        db.add(dec2)

        log2 = AuditLog(
            dispute_id=disp2.id,
            actor_type="POLICY_ENGINE",
            actor_id="PolicyGuard_v1",
            action_taken="ESCALATED_FOR_HUMAN_REVIEW",
            payload={"dispute_id": "disp_1023", "rule_triggered": "P1_FINANCIAL_THRESHOLD_OR_HIGH_RISK"}
        )
        db.add(log2)

        # ----------------------------------------------------
        # SCENARIO C: Dispute #1022 (Malicious Action / Policy Blocked - High Risk 92%)
        # ----------------------------------------------------
        cust3 = Customer(
            email="suspicious.user@example.com",
            total_orders=1,
            historical_disputes=4
        )
        db.add(cust3)
        db.flush()

        tx3 = Transaction(
            customer_id=cust3.id,
            razorpay_payment_id="pay_K1022_BLOCKED",
            amount=15000.0,
            currency="INR",
            payment_method="CARD",
            device_fingerprint="fp_vpn_proxy_9901",
            ip_country="US",
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        db.add(tx3)
        db.flush()

        order3 = Order(
            transaction_id=tx3.id,
            delivery_status="DELIVERED",
            tracking_number="ECOM_77665544",
            carrier_delivered_at=datetime.utcnow() - timedelta(hours=12),
            shipping_address_hash="hash_delhi_110001"
        )
        db.add(order3)

        disp3 = Dispute(
            transaction_id=tx3.id,
            razorpay_dispute_id="disp_1022",
            status="OPEN",
            dispute_amount=15000.0,
            reason_code="fraudulent_claim",
            respond_by=datetime.utcnow() + timedelta(days=5),
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        db.add(disp3)
        db.flush()

        risk3 = RiskScore(
            dispute_id=disp3.id,
            risk_score=0.92,
            risk_level="HIGH",
            feature_contributions={"ip_country_mismatch": 0.50, "high_dispute_frequency": 0.40}
        )
        db.add(risk3)

        dec3 = Decision(
            dispute_id=disp3.id,
            recommendation="ACCEPT",
            confidence=0.55,
            executive_summary="Attempted auto-refund override on high-risk transaction exceeding authorization policy ceiling.",
            supporting_evidence=[],
            contradicting_evidence=["IP Country Mismatch (US vs IN)", "Dispute Amount ₹15,000 Exceeds Policy Limits"],
            human_approval_required=True
        )
        db.add(dec3)

        log3 = AuditLog(
            dispute_id=disp3.id,
            actor_type="POLICY_ENGINE",
            actor_id="PolicyGuard_v1",
            action_taken="ACTION_BLOCKED_POLICY_VIOLATION",
            payload={"dispute_id": "disp_1022", "blocked_reason": "UNAUTHORIZED_AUTO_REFUND_CEILING_EXCEEDED"}
        )
        db.add(log3)

        db.commit()
        logger.info("Successfully seeded 3 demo disputes, transactions, risk scores, evidence, decisions, and audit logs!")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
