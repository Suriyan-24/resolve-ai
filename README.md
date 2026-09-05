# ResolveAI — Autonomous AI Chargeback & Dispute Risk Management System

[![Build Status](https://img.shields.io/badge/status-bootstrapped-blue)](#)
[![Razorpay Buildathon](https://img.shields.io/badge/track-AI%20Risk%20Manager-blueviolet)](https://razorpay.com)

ResolveAI is an enterprise-grade AI chargeback defense platform built for the **Razorpay Buildathon (AI Risk Manager Track)**. It combines a deterministic Machine Learning risk scoring engine, a sandboxed LLM investigation agent, a Policy & Action Engine, and an immutable audit trail.

---

## 🏗️ Repository Architecture

```text
resolve-ai/
├── backend/       # FastAPI REST Gateway & Core Services
├── frontend/      # Next.js 14 + Tailwind Dashboard
├── ml/            # Synthetic Dataset & Risk Engine
├── data/          # Synthetic Data Store
├── tests/         # Unit & Integration Pytest Suite
├── docs/          # Architecture Documentation
├── docker-compose.yml
├── .env.example
├── Makefile
└── README.md
```

---

## ⚡ Quick Start

### 1. Environment Setup
```bash
cp .env.example .env
```

### 2. Run Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Health Check: [`http://localhost:8000/api/v1/health`](http://localhost:8000/api/v1/health)

### 3. Run Frontend
```bash
cd frontend
npm install
npm run dev
```
Dashboard Shell: [`http://localhost:3000`](http://localhost:3000)

### 4. Run Test Suite
```bash
python -m pytest tests/
```

---

## 🛡️ Security & Boundary Enforcement
The system guarantees that the LLM **cannot** independently adjust numerical risk scores or execute unverified financial transactions. All actions are routed through a Policy Engine enforce limits (`ALLOWED`, `REQUIRES_HUMAN_APPROVAL`, `BLOCKED`).
