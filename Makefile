.PHONY: help install-backend install-frontend test-backend test-frontend dev-backend dev-frontend docker-up docker-down

help:
	@echo "ResolveAI Development Commands:"
	@echo "  make install-backend  - Install backend Python dependencies"
	@echo "  make install-frontend - Install frontend Node dependencies"
	@echo "  make test-backend     - Run pytest on backend and ML unit tests"
	@echo "  make dev-backend      - Launch FastAPI development server"
	@echo "  make dev-frontend     - Launch Next.js frontend development server"
	@echo "  make docker-up        - Start all services with Docker Compose"
	@echo "  make docker-down      - Stop all Docker Compose services"

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

test-backend:
	python -m pytest tests/

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down
