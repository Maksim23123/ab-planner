from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models import FcmToken as FcmTokenModel
from app.schemas.fcm_tokens import FcmToken, FcmTokenCreate
from app.services import fcm_token_service

router = APIRouter(prefix="/fcm-tokens", tags=["fcm-tokens"])


@router.get("", response_model=list[FcmToken])
def list_tokens(
    user_id: int | None = Query(default=None, description="Filter by user id"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    target_id = user_id or actor.user.id
    if user_id is not None and actor.role != "admin" and user_id != actor.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return fcm_token_service.list_tokens(db, user_id=target_id)


@router.post("", response_model=FcmToken, status_code=status.HTTP_201_CREATED)
def register_token(
    payload: FcmTokenCreate,
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    target_id = payload.user_id or actor.user.id
    if payload.user_id is not None and actor.role != "admin" and payload.user_id != actor.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return fcm_token_service.register_token(
        db, user_id=target_id, token=payload.token, platform=payload.platform
    )


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_token(
    token_id: int = Path(..., description="Token identifier"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    record = db.get(FcmTokenModel, token_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
    if actor.role != "admin" and record.user_id != actor.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    fcm_token_service.delete_token(db, token_id)
