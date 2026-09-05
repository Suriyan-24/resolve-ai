from fastapi import APIRouter, status
from pydantic import BaseModel
from app.core.config import settings
from app.db.session import check_database_connection

router = APIRouter(prefix="/health", tags=["Health"])

class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    database_connected: bool

@router.get("", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health_check():
    db_ok = check_database_connection()
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        app_name=settings.APP_NAME,
        environment=settings.ENV,
        database_connected=db_ok
    )
