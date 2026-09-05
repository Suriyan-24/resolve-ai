# ResolveAI — Autonomous AI Chargeback & Dispute Risk Management System

[![Build Status](https://img.shields.io/badge/status-submission--ready-success)](#)
[![Razorpay Buildathon](https://img.shields.io/badge/track-AI%20Risk%20Manager-blueviolet)](https://razorpay.com)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.14-blue)](#)
[![Next.js](https://img.shields.io/badge/next.js-14.2-black)](#)

ResolveAI is an enterprise-grade AI chargeback defense platform built for the **Razorpay Buildathon (AI Risk Manager Track)**. It combines a deterministic Machine Learning risk scoring engine, a sandboxed LLM investigation agent, a Policy & Action Engine, and an immutable audit trail.

---

## 🎯 Problem & Core Mission

E-commerce merchants lose billions annually to "friendly fraud" and chargeback disputes. Traditional manual dispute management is slow, expensive, and error-prone. Conversely, unconstrained LLM automation risks unsafe financial operations and unintended liability acceptance.

**ResolveAI solves this with a strict separation of concerns**:
1. **ML Risk Engine**: Quantifies dispute fraud probability ($S \in [0.0, 1.0]$) deterministically.
2. **AI Investigator Agent**: Autonomous multi-step evidence gathering and structured reasoning.
3. **Policy & Action Engine**: Deterministic safety boundary enforcing financial limits and human approval guardrails.
4. **Immutable Audit Trail**: Cryptographic compliance record of all decisions and actions.

---

## 🏗️ Repository Architecture

```text
resolve-ai/
├── backend/               # FastAPI Gateway & Services
│   ├── app/
│   │   ├── api/v1/       # REST Routes (disputes, actions, audit, webhooks, health)
│   │   ├── core/         # Config & Logging
│   │   ├── db/           # SQLAlchemy Schemas & Repositories
│   │   ├── services/     # PolicyEngine, AIAgentInvestigator, RazorpayAdapter
│   │   └── tools/        # Sandboxed Dispute Investigation Tools
├── frontend/              # Next.js 14 + Tailwind Dashboard
│   └── src/app/          # App Router Pages (Command Center, Hero Screen, Trace, Audit)
├── ml/                    # Machine Learning Risk Pipeline
│   ├── dataset_generator.py # Synthetic Dataset Generator
│   ├── train.py           # Model Training & Held-Out Test Evaluation
│   ├── risk_engine.py     # Deterministic ML Inference Engine
│   └── models/            # Exported Joblib Model Artifact (risk_model_v1.joblib)
├── scripts/
│   ├── seed_db.py         # Database Seeding Script (3 Demo Scenarios)
│   ├── evaluate_agent.py  # Agent & Policy Benchmark Evaluation Script
│   └── demo_simulation.py # End-to-End Buildathon Demo Script
├── tests/                 # Comprehensive Pytest Suite (22 Unit & Integration Tests)
├── docs/                  # Architecture & ML Evaluation Reports
├── docker-compose.yml
├── .env.example
├── pyproject.toml
└── README.md
```

---

## ⚡ Quick Start

### 1. Environment Setup
```bash
cp .env.example .env
```

### 2. Run Database Seeding
```bash
python scripts/seed_db.py
```

### 3. Run Backend Gateway
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Health Check: [`http://localhost:8000/api/v1/health`](http://localhost:8000/api/v1/health)

### 4. Run Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```
Dashboard Shell: [`http://localhost:3000`](http://localhost:3000)

---

## 🧪 Testing & Evaluation Commands

### Run Full Pytest Suite (22 Tests)
```bash
python -m pytest tests/
```

### Run ML Training & Held-Out Test Evaluation
```bash
python -m ml.train
```

### Run Agent & Policy Benchmark Evaluation
```bash
python scripts/evaluate_agent.py
```

### Run End-to-End Buildathon Demo Simulation
```bash
python scripts/demo_simulation.py
```

### Build Next.js Production Bundle
```bash
cd frontend
npm run build
```

---

## 🛡️ Security & Boundary Enforcement

The LLM **cannot** independently alter risk scores or execute unverified financial transactions.

```text
AI Recommendation (DEFEND / REVIEW / ACCEPT)
                     │
                     ▼
          ┌─────────────────────┐
          │    Policy Engine    │
          └──────────┬──────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
      ALLOWED     REVIEW      BLOCKED
```

### Policy Guardrail Rules:
* **P1 State Idempotency**: Prevents duplicate execution on finalized disputes (`DEFENDED`, `ACCEPTED`).
* **P2 Financial Ceiling**: Escalates automated defense for disputes $> \text{INR } 5,000$ to mandatory human review.
* **P3 Confidence Threshold**: Escalates recommendations with $< 85\%$ confidence.
* **P4 Auto-Accept Guard**: Prohibits automated acceptance of high-risk disputes ($\ge 70\%$).
* **P5 Evidence Guard**: Blocks chargeback defense submission without verified evidence.
* **P6 Human Override**: Explicit human user authorization override.
* **P7 High-Risk Escalation**: Mandates human review for high-risk automated actions.

---

## 📈 ML Risk Engine Performance

Evaluated on held-out test dataset ($N = 1,500$):

* **Precision**: $96.45\%$
* **Recall**: $93.68\%$
* **F1-Score**: $95.04\%$
* **ROC-AUC**: $0.9987$
* **False Positive Rate**: $0.45\%$
* **False Negative Rate**: $6.32\%$

Full details available in [`docs/ml_evaluation_report.md`](file:///c:/Users/Admin/.gemini/antigravity-ide/scratch/resolve-ai/docs/ml_evaluation_report.md).

---

## ⚠️ Synthetic Data Limitations & Future Roadmap

* **Synthetic Data**: Evaluation is conducted on synthetic transaction data (`dataset_generator.py`). Production deployment requires fine-tuning on live merchant logs.
* **Live Razorpay Webhooks**: Production integration connects to Razorpay live Webhooks (`/api/v1/webhooks/razorpay`) with constant-time HMAC signature verification.
