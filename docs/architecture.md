# ResolveAI Architecture Reference

## 🏛️ System Architecture

ResolveAI enforces a strict separation of concerns between quantitative ML risk scoring, LLM evidence investigation, deterministic policy boundaries, and gateway integrations.

```text
                  ┌───────────────────────────────┐
                  │    Razorpay Webhook Ingest    │
                  └──────────────┬────────────────┘
                                 │ HMAC Signature & Deduplication
                                 ▼
                  ┌───────────────────────────────┐
                  │    FastAPI Gateway Router     │
                  └──────────────┬────────────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
┌─────────────────────┐                     ┌─────────────────────┐
│  ML Risk Engine     │                     │  AI Investigator    │
│  (Deterministic)    │                     │  (Bounded Tools)    │
│  $S \in [0.0, 1.0]$ │                     │  Tool Traces        │
└──────────┬──────────┘                     └──────────┬──────────┘
           │                                           │
           └─────────────────────┬─────────────────────┘
                                 │ Evidence & Score
                                 ▼
                  ┌───────────────────────────────┐
                  │    Policy & Action Engine     │
                  │   (Deterministic Boundary)    │
                  │   ALLOWED / REVIEW / BLOCKED  │
                  └──────────────┬────────────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
┌─────────────────────┐                     ┌─────────────────────┐
│   Razorpay Test     │                     │  Immutable Audit    │
│   Adapter / Mock    │                     │  Trail Repository   │
└─────────────────────┘                     └─────────────────────┘
```

---

## 🔒 Strict Separation of Concerns

1. **ML Risk Engine (`ml/risk_engine.py`)**:
   * Evaluates quantitative risk features ($S \in [0.0, 1.0]$).
   * Operates deterministically via trained scikit-learn model artifacts (`ml/models/risk_model_v1.joblib`).
   * **Boundary**: Cannot generate natural language or execute API actions.

2. **AI Investigator Agent (`backend/app/services/agent_service.py`)**:
   * Sandboxed tool execution via `DisputeToolRegistry` (`get_transaction`, `get_customer_history`, `get_order_and_delivery`, `get_previous_disputes`, `get_risk_analysis`).
   * Multi-step evidence synthesis and executive summary generation.
   * Supports external LLM providers (Gemini / OpenAI) with automatic fallback to local rule-based synthesis.
   * **Boundary**: Cannot modify numerical risk scores or execute financial transactions directly.

3. **Policy & Action Engine (`backend/app/services/policy_service.py`)**:
   * The ultimate deterministic authority for all consequential actions.
   * **Rules Enforced**:
     * `P1_STATE_FINALIZED_IDEMPOTENCY`: Prevents re-acting on finalized disputes (`DEFENDED`, `ACCEPTED`).
     * `P2_FINANCIAL_AMOUNT_CEILING`: Escalates disputes exceeding ₹5,000 to mandatory human review.
     * `P3_LOW_CONFIDENCE_ESCALATION`: Escalates recommendations with $< 85\%$ confidence.
     * `P4_HIGH_RISK_AUTO_ACCEPT_PROHIBITED`: Blocks automated acceptance of disputes with risk score $\ge 70\%$.
     * `P5_MISSING_EVIDENCE_GUARD`: Blocks submission of chargeback defense without verified evidence.
     * `P6_HUMAN_EXPLICIT_AUTHORIZATION`: Explicit human user override authorization.
     * `P7_HIGH_RISK_HUMAN_REVIEW_REQUIRED`: Mandates human review for high-risk automated actions.

4. **Razorpay Integration Adapter (`backend/app/services/razorpay_adapter.py`)**:
   * Abstract `PaymentProvider` interface supporting `MockPaymentProvider` (local dev) and `RazorpayTestProvider`.
   * Constant-time HMAC-SHA256 signature verification (`hmac.compare_digest`).

5. **Immutable Audit Trail (`backend/app/db/models.py`)**:
   * Every decision, investigation trace, and policy outcome is recorded in the `audit_logs` table for complete auditability.
