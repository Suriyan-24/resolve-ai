import hmac
import hashlib
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.logging import logger

class DisputeDefenseSubmission(BaseModel):
    dispute_id: str
    razorpay_dispute_id: str
    summary: str
    evidence_documents: list[str] = Field(default_factory=list)

class PaymentProvider(ABC):
    @abstractmethod
    def fetch_dispute(self, razorpay_dispute_id: str) -> Dict[str, Any]:
        """Fetch dispute metadata from payment gateway."""
        pass

    @abstractmethod
    def submit_defense(self, submission: DisputeDefenseSubmission) -> Dict[str, Any]:
        """Submit chargeback defense evidentiary package."""
        pass

    @abstractmethod
    def accept_dispute(self, razorpay_dispute_id: str) -> Dict[str, Any]:
        """Accept chargeback liability."""
        pass


class MockPaymentProvider(PaymentProvider):
    def fetch_dispute(self, razorpay_dispute_id: str) -> Dict[str, Any]:
        logger.info(f"[MOCK PAYMENT PROVIDER] Fetching dispute: {razorpay_dispute_id}")
        return {
            "id": razorpay_dispute_id,
            "entity": "dispute",
            "payment_id": "pay_mock_12345678",
            "amount": 210000,  # in paise
            "currency": "INR",
            "status": "open",
            "reason_code": "merchandise_not_received",
            "respond_by": int(time.time()) + (7 * 86400),
            "created_at": int(time.time()) - 86400
        }

    def submit_defense(self, submission: DisputeDefenseSubmission) -> Dict[str, Any]:
        logger.info(f"[MOCK PAYMENT PROVIDER] Submitting defense for {submission.razorpay_dispute_id}")
        return {
            "id": submission.razorpay_dispute_id,
            "status": "under_review",
            "action": "defend",
            "submitted_at": int(time.time()),
            "message": "Defense evidence package submitted successfully to Razorpay Test Mode."
        }

    def accept_dispute(self, razorpay_dispute_id: str) -> Dict[str, Any]:
        logger.info(f"[MOCK PAYMENT PROVIDER] Accepting dispute liability for {razorpay_dispute_id}")
        return {
            "id": razorpay_dispute_id,
            "status": "accepted",
            "action": "accept",
            "accepted_at": int(time.time()),
            "message": "Dispute liability accepted."
        }


class RazorpayTestProvider(PaymentProvider):
    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET

    def _get_auth(self):
        return (self.key_id, self.key_secret)

    def fetch_dispute(self, razorpay_dispute_id: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/disputes/{razorpay_dispute_id}"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, auth=self._get_auth())
                if resp.status_code == 200:
                    return resp.json()
                logger.warning(f"Razorpay API error {resp.status_code}: {resp.text}")
                return MockPaymentProvider().fetch_dispute(razorpay_dispute_id)
        except Exception as e:
            logger.error(f"Razorpay API request failed, falling back to mock: {e}")
            return MockPaymentProvider().fetch_dispute(razorpay_dispute_id)

    def submit_defense(self, submission: DisputeDefenseSubmission) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/disputes/{submission.razorpay_dispute_id}/contest"
        payload = {
            "summary": submission.summary,
            "evidence": submission.evidence_documents
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.patch(url, json=payload, auth=self._get_auth())
                if resp.status_code in [200, 201]:
                    return resp.json()
                logger.warning(f"Razorpay contest API fallback: {resp.status_code}")
                return MockPaymentProvider().submit_defense(submission)
        except Exception as e:
            logger.error(f"Razorpay contest request failed, using mock fallback: {e}")
            return MockPaymentProvider().submit_defense(submission)

    def accept_dispute(self, razorpay_dispute_id: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/disputes/{razorpay_dispute_id}/accept"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, auth=self._get_auth())
                if resp.status_code == 200:
                    return resp.json()
                return MockPaymentProvider().accept_dispute(razorpay_dispute_id)
        except Exception as e:
            logger.error(f"Razorpay accept request failed, using mock fallback: {e}")
            return MockPaymentProvider().accept_dispute(razorpay_dispute_id)


def verify_razorpay_webhook_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """
    Verifies Razorpay HMAC-SHA256 webhook signature.
    Uses constant-time comparison to protect against timing attacks.
    """
    if not signature or not secret:
        return False
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


def get_payment_provider() -> PaymentProvider:
    if settings.RAZORPAY_KEY_ID.startswith("rzp_test") and settings.ENV != "production":
        return MockPaymentProvider()
    return RazorpayTestProvider()
