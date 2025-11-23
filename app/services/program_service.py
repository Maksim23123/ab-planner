from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Group, Program


def list_programs(db: Session) -> list[Program]:
    stmt = (
        select(Program)
        .options(
            joinedload(Program.years),
            joinedload(Program.specializations),
        )
        .order_by(Program.id)
    )
    return list(db.scalars(stmt).all())


def list_groups(
    db: Session,
    *,
    program_id: int | None = None,
    program_year_id: int | None = None,
    specialization_id: int | None = None,
    group_type: str | None = None,
) -> list[Group]:
    stmt = select(Group).options(
        joinedload(Group.program),
        joinedload(Group.program_year),
        joinedload(Group.specialization),
        joinedload(Group.group_type),
    )

    if program_id is not None:
        stmt = stmt.where(Group.program_id == program_id)
    if program_year_id is not None:
        stmt = stmt.where(Group.program_year_id == program_year_id)
    if specialization_id is not None:
        stmt = stmt.where(Group.specialization_id == specialization_id)
    if group_type is not None:
        stmt = stmt.where(Group.group_type_code == group_type)

    stmt = stmt.order_by(Group.id)
    return list(db.scalars(stmt).all())


def get_group(db: Session, group_id: int) -> Group:
    stmt = select(Group).options(
        joinedload(Group.program),
        joinedload(Group.program_year),
        joinedload(Group.specialization),
        joinedload(Group.group_type),
    ).where(Group.id == group_id)

    group = db.execute(stmt).scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group
