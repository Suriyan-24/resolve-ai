# ResolveAI Architecture Reference

## Component Breakdown

1. **Backend Gateway (`backend/app/main.py`)**:
   - Built on FastAPI with Pydantic schema validation.
   - Standardized structured JSON logging and exception handlers.
   - Exposes `/api/v1/health` for uptime and DB connection status checks.

2. **Database Engine (`backend/app/db/session.py`)**:
   - Uses SQLAlchemy 2.0.
   - Supports PostgreSQL in production and SQLite for zero-dependency local testing.

3. **Machine Learning Risk Engine (`ml/`)**:
   - Implements `AbstractRiskEngine` interface contract.
   - Computes deterministic numerical risk scores $S \in [0.0, 1.0]$.

4. **Policy Engine (`backend/app/services/policy_service.py` - Scaffolding)**:
   - Evaluates actions against safety state machine: `ALLOWED`, `REQUIRES_HUMAN_APPROVAL`, `BLOCKED`.

5. **Frontend Dashboard (`frontend/`)**:
   - Next.js 14 application shell styled with Tailwind CSS.
   - Features real-time API connectivity monitoring.
