from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories import AuditRepository
from app.db.models import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.get("", status_code=status.HTTP_200_OK)
def list_audit_logs(
    dispute_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if dispute_id:
        query = query.filter(AuditLog.dispute_id == dispute_id)
    
    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

    result = []
    for l in logs:
        result.append({
            "id": l.id,
            "dispute_id": l.dispute_id,
            "actor_type": l.actor_type,
            "actor_id": l.actor_id,
            "action_taken": l.action_taken,
            "payload": l.payload,
            "timestamp": str(l.timestamp)
        })
    return result
