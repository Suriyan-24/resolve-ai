from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.api.v1.health import router as health_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.disputes import router as disputes_router
from app.api.v1.actions import router as actions_router
from app.api.v1.audit import router as audit_router
from app.db.session import Base, engine

# Create tables for dev engine automatically if needed
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="ResolveAI Chargeback & Dispute Risk Management System Gateway",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")
app.include_router(disputes_router, prefix="/api/v1")
app.include_router(actions_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API Gateway",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

logger.info(f"FastAPI gateway initialized for {settings.APP_NAME}")
