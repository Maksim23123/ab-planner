from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Role, User
from app.services.audit_service import record_change, serialize_model


def _with_role():
    return joinedload(User.role)


def _get_role_by_id(db: Session, role_id: int) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


def _ensure_role_mutable(user: User) -> None:
    current = (getattr(user.role, "code", "") or "").lower()
    if current == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin role cannot be changed via API",
        )


def _normalize_role(role: str) -> str:
    return role.lower()


def _ensure_assignable_role(role: Role) -> str:
    normalized = _normalize_role(role.code)
    if normalized == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigning admin role via API is not allowed",
        )
    if normalized not in {"student", "lecturer"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be either 'student' or 'lecturer'",
        )
    return normalized


def get_user_profile(db: Session, user_id: int) -> User:
    """Fetch a user with their role for profile payloads."""
    stmt = select(User).options(_with_role()).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def list_users(db: Session) -> list[User]:
    stmt = select(User).options(_with_role()).order_by(User.id)
    return list(db.scalars(stmt).all())


def get_user(db: Session, user_id: int) -> User:
    return get_user_profile(db, user_id)


def set_user_role(db: Session, user_id: int, target_role_id: int, *, actor_user_id: int) -> User:
    user = get_user_profile(db, user_id)
    _ensure_role_mutable(user)

    target_role = _get_role_by_id(db, target_role_id)
    desired = _ensure_assignable_role(target_role)
    current_role = _normalize_role(getattr(user.role, "code", "") or "")
    if current_role == desired:
        return user

    before = serialize_model(user)
    user.role_id = target_role.id
    db.flush()
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=User.__tablename__,
        entity_id=user.id,
        action="update",
        old_data=before,
        new_data=serialize_model(user),
    )
    db.commit()
    db.refresh(user)
    return get_user_profile(db, user.id)
