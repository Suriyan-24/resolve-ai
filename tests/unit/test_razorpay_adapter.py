import hmac
import hashlib
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.razorpay_adapter import (
    MockPaymentProvider, RazorpayTestProvider, 
    verify_razorpay_webhook_signature, DisputeDefenseSubmission
)

client = TestClient(app)

def test_mock_payment_provider_methods():
    provider = MockPaymentProvider()

    dispute_info = provider.fetch_dispute("disp_mock_999")
    assert dispute_info["id"] == "disp_mock_999"
    assert dispute_info["amount"] == 210000

    sub = DisputeDefenseSubmission(
        dispute_id="d1",
        razorpay_dispute_id="disp_mock_999",
        summary="Proof of delivery attached",
        evidence_documents=["doc_1.pdf"]
    )
    def_res = provider.submit_defense(sub)
    assert def_res["status"] == "under_review"

    acc_res = provider.accept_dispute("disp_mock_999")
    assert acc_res["status"] == "accepted"


def test_hmac_webhook_signature_verification():
    secret = "test_webhook_secret_12345"
    body = b'{"event":"dispute.created","event_id":"evt_sig_test_1"}'

    valid_signature = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()

    # 1. Valid signature check
    assert verify_razorpay_webhook_signature(body, valid_signature, secret) is True

    # 2. Tampered signature check
    assert verify_razorpay_webhook_signature(body, "invalid_sig_hash_999", secret) is False

    # 3. Tampered payload check
    tampered_body = b'{"event":"dispute.created","event_id":"evt_sig_test_1_HACKED"}'
    assert verify_razorpay_webhook_signature(tampered_body, valid_signature, secret) is False


def test_webhook_endpoint_ingestion_and_deduplication():
    uid = str(uuid.uuid4())[:8]
    event_id = f"evt_webhook_test_{uid}"
    payload = {
        "event_id": event_id,
        "event": "dispute.created",
        "payload": {
            "dispute": {
                "entity": {
                    "id": f"disp_wh_{uid}",
                    "payment_id": f"pay_wh_{uid}",
                    "amount": 250000,
                    "reason_code": "merchandise_not_received"
                }
            }
        }
    }

    # First webhook post (with dev mock signature header)
    resp1 = client.post(
        "/api/v1/webhooks/razorpay",
        json=payload,
        headers={"X-Razorpay-Signature": "mock_signature_for_dev"}
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "processed"
    assert data1["event_id"] == event_id

    # Duplicate webhook post (replay attempt)
    resp2 = client.post(
        "/api/v1/webhooks/razorpay",
        json=payload,
        headers={"X-Razorpay-Signature": "mock_signature_for_dev"}
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "ignored_duplicate"
