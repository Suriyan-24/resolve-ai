import time
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.repositories import DisputeRepository, CustomerRepository
from app.db.models import Transaction, Order, Dispute, Customer, Evidence
from ml.risk_engine import MLRiskEngine
from app.core.logging import logger

class ToolTraceEntry(BaseModel):
    tool_name: str
    input_params: Dict[str, Any]
    output_summary: Dict[str, Any]
    duration_ms: float
    timestamp: str

class DisputeToolRegistry:
    def __init__(self, db: Session):
        self.db = db
        self.dispute_repo = DisputeRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.risk_engine = MLRiskEngine()

    def get_transaction(self, dispute_id: str) -> Dict[str, Any]:
        """Retrieves transaction payment method, amount, timestamp, IP country, and device fingerprint."""
        start = time.time()
        dispute = self.dispute_repo.get_by_id(dispute_id)
        if not dispute or not dispute.transaction:
            return {"error": f"Transaction for dispute {dispute_id} not found."}

        tx: Transaction = dispute.transaction
        result = {
            "transaction_id": tx.id,
            "razorpay_payment_id": tx.razorpay_payment_id,
            "amount": tx.amount,
            "currency": tx.currency,
            "payment_method": tx.payment_method,
            "device_fingerprint": tx.device_fingerprint,
            "ip_country": tx.ip_country,
            "created_at": str(tx.created_at)
        }
        logger.info(f"TOOL get_transaction({dispute_id}) executed in {(time.time()-start)*1000:.2f}ms")
        return result

    def get_customer_history(self, customer_id: str) -> Dict[str, Any]:
        """Retrieves customer total order history, account creation date, and past dispute count."""
        start = time.time()
        customer = self.customer_repo.get_by_id(customer_id)
        if not customer:
            return {"error": f"Customer {customer_id} not found."}

        result = {
            "customer_id": customer.id,
            "email": customer.email,
            "total_orders": float(customer.total_orders or 0),
            "historical_disputes": float(customer.historical_disputes or 0),
            "account_created_at": str(customer.account_created_at)
        }
        logger.info(f"TOOL get_customer_history({customer_id}) executed in {(time.time()-start)*1000:.2f}ms")
        return result

    def get_order_and_delivery(self, transaction_id: str) -> Dict[str, Any]:
        """Retrieves shipping status, carrier tracking number, delivery timestamp, and address hash."""
        start = time.time()
        order = self.db.query(Order).filter(Order.transaction_id == transaction_id).first()
        if not order:
            return {"error": f"Order for transaction {transaction_id} not found."}

        result = {
            "order_id": order.id,
            "delivery_status": order.delivery_status,
            "tracking_number": order.tracking_number,
            "carrier_delivered_at": str(order.carrier_delivered_at) if order.carrier_delivered_at else None,
            "shipping_address_hash": order.shipping_address_hash
        }
        logger.info(f"TOOL get_order_and_delivery({transaction_id}) executed in {(time.time()-start)*1000:.2f}ms")
        return result

    def get_previous_disputes(self, customer_id: str) -> Dict[str, Any]:
        """Retrieves all previous dispute filings associated with a customer."""
        start = time.time()
        disputes = (
            self.db.query(Dispute)
            .join(Transaction)
            .filter(Transaction.customer_id == customer_id)
            .all()
        )

        records = []
        for d in disputes:
            records.append({
                "dispute_id": d.id,
                "razorpay_dispute_id": d.razorpay_dispute_id,
                "amount": d.dispute_amount,
                "reason_code": d.reason_code,
                "status": d.status
            })

        result = {
            "customer_id": customer_id,
            "total_disputes_found": len(records),
            "disputes": records
        }
        logger.info(f"TOOL get_previous_disputes({customer_id}) executed in {(time.time()-start)*1000:.2f}ms")
        return result

    def get_risk_analysis(self, dispute_id: str) -> Dict[str, Any]:
        """Retrieves deterministic numerical risk score and feature contributions from ML Risk Engine."""
        start = time.time()
        dispute = self.dispute_repo.get_by_id(dispute_id)
        if not dispute or not dispute.transaction:
            return {"error": f"Dispute {dispute_id} not found for risk analysis."}

        tx = dispute.transaction
        cust = tx.customer
        order = tx.order

        features = {
            "transaction_amount": tx.amount,
            "account_age_days": 180,
            "previous_orders": float(cust.total_orders if cust else 1),
            "previous_disputes": float(cust.historical_disputes if cust else 0),
            "refund_count_30d": 1 if (cust and float(cust.historical_disputes or 0) > 0) else 0,
            "carrier_delivery_gap_hours": 48.0,
            "device_change_flag": "unknown" in tx.device_fingerprint or "vpn" in tx.device_fingerprint,
            "ip_country_mismatch": tx.ip_country != "IN",
            "order_velocity_24h": 1,
            "amount_vs_historical_avg_ratio": round(tx.amount / 2000.0, 2),
            "delivery_confirmation_valid": order.delivery_status == "DELIVERED" if order else False
        }

        risk_res = self.risk_engine.predict_risk(features)
        result = {
            "dispute_id": dispute_id,
            "risk_score": risk_res.risk_score,
            "risk_level": risk_res.risk_level,
            "feature_contributions": risk_res.feature_contributions,
            "model_version": risk_res.model_version
        }
        logger.info(f"TOOL get_risk_analysis({dispute_id}) executed in {(time.time()-start)*1000:.2f}ms")
        return result
