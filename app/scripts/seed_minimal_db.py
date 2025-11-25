# Bash command to run: python -m app.scripts.seed_minimal_db
from __future__ import annotations

from datetime import datetime, timezone
from typing import Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import mock_data
from app.core.config import get_settings
from app.core.database import SessionLocal, ensure_database
from app.core.run_migrations import ensure_schema_up_to_date
from app.models import GroupType, Role, User


ESSENTIAL_ROLE_CODES = {"student", "lecturer", "admin"}


def _ensure_roles(session: Session, *, default_role_code: str) -> Tuple[int, int]:
    """Insert or update the minimal role set."""
    existing = {role.code: role for role in session.scalars(select(Role)).all()}
    created = updated = 0

    for payload in mock_data.ROLES:
        code = payload["code"]
        if code not in ESSENTIAL_ROLE_CODES:
            continue

        record = existing.get(code)
        if record is None:
            session.add(Role(code=code, label=payload["label"]))
            created += 1
        elif record.label != payload["label"]:
            record.label = payload["label"]
            updated += 1

    session.flush()
    if session.scalar(select(Role).where(Role.code == default_role_code)) is None:
        raise RuntimeError(
            f"Default role '{default_role_code}' is missing; update AUTH_DEFAULT_ROLE or seed it first."
        )

    return created, updated


def _ensure_group_types(session: Session) -> Tuple[int, int]:
    """Insert or update group types used as reference data."""
    existing = {item.code: item for item in session.scalars(select(GroupType)).all()}
    created = updated = 0

    for payload in mock_data.GROUP_TYPES:
        code = payload["code"]
        record = existing.get(code)
        if record is None:
            session.add(GroupType(code=code, label=payload["label"]))
            created += 1
        elif record.label != payload["label"]:
            record.label = payload["label"]
            updated += 1

    return created, updated


def _ensure_admin_user(session: Session, *, email: str, name: str) -> Tuple[bool, bool]:
    """Guarantee at least one admin user exists to access privileged endpoints."""
    admin_role = session.scalar(select(Role).where(Role.code == "admin"))
    if admin_role is None:
        raise RuntimeError("Admin role missing; seed roles first.")

    user = session.scalar(select(User).where(User.email == email))
    created = updated = False

    if user is None:
        user = User(
            email=email,
            name=name,
            role_id=admin_role.id,
            created_at=datetime.now(timezone.utc),
        )
        session.add(user)
        created = True
    else:
        if user.role_id != admin_role.id:
            user.role_id = admin_role.id
            updated = True
        if user.name != name:
            user.name = name
            updated = True

    return created, updated


def seed_minimal() -> None:
    """Seed only the reference data required for the API to work."""
    ensure_database()
    ensure_schema_up_to_date()

    settings = get_settings()
    admin_email = settings.admin_email.lower()
    admin_name = settings.admin_name
    seed_admin = bool(settings.seed_admin)

    with SessionLocal() as session:
        with session.begin():
            roles_created, roles_updated = _ensure_roles(
                session, default_role_code=settings.auth_default_role_code
            )
            group_types_created, group_types_updated = _ensure_group_types(session)
            admin_created = admin_updated = False
            if seed_admin:
                admin_created, admin_updated = _ensure_admin_user(
                    session, email=admin_email, name=admin_name
                )

    print("Essential data seeded:")
    print(f"- Roles: {roles_created} created, {roles_updated} updated")
    print(f"- Group types: {group_types_created} created, {group_types_updated} updated")
    if seed_admin:
        if admin_created or admin_updated:
            action = "created" if admin_created else "updated"
            print(f"- Admin user {action}: {admin_email}")
        else:
            print(f"- Admin user unchanged: {admin_email}")
    else:
        print("- Admin user skipped (set SEED_ADMIN=true to create)")


if __name__ == "__main__":
    seed_minimal()
