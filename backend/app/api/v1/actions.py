from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.policy_service import (
    PolicyEngine, ActionRequest, ActionResponse, 
    ActionType, ActorType
)

router = APIRouter(prefix="/actions", tags=["Actions"])

@router.post("/execute", response_model=ActionResponse, status_code=status.HTTP_200_OK)
def execute_policy_action(req: ActionRequest, db: Session = Depends(get_db)):
    engine = PolicyEngine(db)
    response = engine.execute_action(req)
    return response
