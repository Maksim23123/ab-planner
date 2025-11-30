from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import Group, Program, ProgramYear, Specialization, GroupType
from app.services.audit_service import record_change, serialize_model


def list_programs(db: Session) -> list[Program]:
    stmt = (
        select(Program)
        .options(
            joinedload(Program.years),
            joinedload(Program.specializations),
        )
        .order_by(Program.id)
    )
    return list(db.execute(stmt).unique().scalars().all())


def get_program(db: Session, program_id: int) -> Program:
    stmt = (
        select(Program)
        .options(
            joinedload(Program.years),
            joinedload(Program.specializations),
        )
        .where(Program.id == program_id)
    )
    program = db.execute(stmt).unique().scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    return program


def create_program(db: Session, name: str, *, actor_user_id: int) -> Program:
    program = Program(name=name)
    db.add(program)
    db.flush()
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=Program.__tablename__,
        entity_id=program.id,
        action="create",
        old_data=None,
        new_data=serialize_model(program),
    )
    db.commit()
    db.refresh(program)
    return program


def update_program(
    db: Session, program_id: int, *, name: str | None = None, actor_user_id: int
) -> Program:
    program = db.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    before = serialize_model(program)
    if name is not None:
        program.name = name
    db.flush()
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=Program.__tablename__,
        entity_id=program.id,
        action="update",
        old_data=before,
        new_data=serialize_model(program),
    )
    db.commit()
    db.refresh(program)
    return get_program(db, program.id)


def delete_program(db: Session, program_id: int, *, actor_user_id: int) -> None:
    program = db.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    before = serialize_model(program)
    _safe_delete(
        db,
        program,
        detail="Program is still in use",
        audit_log={
            "actor_user_id": actor_user_id,
            "entity": Program.__tablename__,
            "entity_id": program.id,
            "action": "delete",
            "old_data": before,
            "new_data": None,
        },
    )


def list_program_years(db: Session) -> list[ProgramYear]:
    stmt = select(ProgramYear).options(joinedload(ProgramYear.program)).order_by(ProgramYear.id)
    return list(db.scalars(stmt).all())


def get_program_year(db: Session, year_id: int) -> ProgramYear:
    stmt = (
        select(ProgramYear).options(joinedload(ProgramYear.program)).where(ProgramYear.id == year_id)
    )
    program_year = db.execute(stmt).scalar_one_or_none()
    if not program_year:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program year not found")
    return program_year


def create_program_year(
    db: Session, program_id: int, year: int, *, actor_user_id: int
) -> ProgramYear:
    if db.get(Program, program_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    record = ProgramYear(program_id=program_id, year=year)
    db.add(record)
    db.flush()
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=ProgramYear.__tablename__,
        entity_id=record.id,
        action="create",
        old_data=None,
        new_data=serialize_model(record),
    )
    db.commit()
    db.refresh(record)
    return get_program_year(db, record.id)


def update_program_year(
    db: Session,
    year_id: int,
    *,
    year: int | None = None,
    program_id: int | None = None,
    actor_user_id: int,
) -> ProgramYear:
    record = db.get(ProgramYear, year_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program year not found")
    before = serialize_model(record)
    if program_id is not None and db.get(Program, program_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    if program_id is not None and program_id != record.program_id:
        in_use = db.scalar(select(Group.id).where(Group.program_year_id == year_id).limit(1))
        if in_use is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Program year is still linked to groups and cannot change program",
            )
    if program_id is not None:
        record.program_id = program_id
    if year is not None:
        record.year = year
    db.flush()
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=ProgramYear.__tablename__,
        entity_id=record.id,
        action="update",
        old_data=before,
        new_data=serialize_model(record),
    )
    db.commit()
    db.refresh(record)
    return get_program_year(db, record.id)


def delete_program_year(db: Session, year_id: int, *, actor_user_id: int) -> None:
    record = db.get(ProgramYear, year_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program year not found")
    before = serialize_model(record)
    _safe_delete(
        db,
        record,
        detail="Program year is still in use",
        audit_log={
            "actor_user_id": actor_user_id,
            "entity": ProgramYear.__tablename__,
            "entity_id": record.id,
            "action": "delete",
            "old_data": before,
            "new_data": None,
        },
    )


def list_specializations(db: Session) -> list[Specialization]:
    stmt = select(Specialization).options(joinedload(Specialization.program)).order_by(Specialization.id)
    return list(db.scalars(stmt).all())


def get_specialization(db: Session, spec_id: int) -> Specialization:
    stmt = (
        select(Specialization)
        .options(joinedload(Specialization.program))
        .where(Specialization.id == spec_id)
    )
    spec = db.execute(stmt).scalar_one_or_none()
    if not spec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialization not found")
    return spec


def create_specialization(
    db: Session, program_id: int, name: str, *, actor_user_id: int
) -> Specialization:
    if db.get(Program, program_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    spec = Specialization(program_id=program_id, name=name)
    db.add(spec)
    db.flush()
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=Specialization.__tablename__,
        entity_id=spec.id,
        action="create",
        old_data=None,
        new_data=serialize_model(spec),
    )
    db.commit()
    db.refresh(spec)
    return get_specialization(db, spec.id)


def update_specialization(
    db: Session,
    spec_id: int,
    *,
    name: str | None = None,
    program_id: int | None = None,
    actor_user_id: int,
) -> Specialization:
    spec = db.get(Specialization, spec_id)
    if not spec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialization not found")
    before = serialize_model(spec)
    if program_id is not None and db.get(Program, program_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    if program_id is not None and program_id != spec.program_id:
        in_use = db.scalar(select(Group.id).where(Group.specialization_id == spec_id).limit(1))
        if in_use is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Specialization is still linked to groups and cannot change program",
            )
    if program_id is not None:
        spec.program_id = program_id
    if name is not None:
        spec.name = name
    db.flush()
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=Specialization.__tablename__,
        entity_id=spec.id,
        action="update",
        old_data=before,
        new_data=serialize_model(spec),
    )
    db.commit()
    db.refresh(spec)
    return get_specialization(db, spec.id)


def delete_specialization(db: Session, spec_id: int, *, actor_user_id: int) -> None:
    spec = db.get(Specialization, spec_id)
    if not spec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialization not found")
    before = serialize_model(spec)
    _safe_delete(
        db,
        spec,
        detail="Specialization is still in use",
        audit_log={
            "actor_user_id": actor_user_id,
            "entity": Specialization.__tablename__,
            "entity_id": spec.id,
            "action": "delete",
            "old_data": before,
            "new_data": None,
        },
    )


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
    stmt = (
        select(Group)
        .options(
            joinedload(Group.program),
            joinedload(Group.program_year),
            joinedload(Group.specialization),
            joinedload(Group.group_type),
        )
        .where(Group.id == group_id)
    )

    group = db.execute(stmt).scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


def _ensure_group_type(db: Session, code: str) -> None:
    if db.get(GroupType, code) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group type not found")


def _safe_delete(
    db: Session, record, *, detail: str, audit_log: dict[str, Any] | None = None
) -> None:
    try:
        db.delete(record)
        if audit_log:
            record_change(db, **audit_log)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def _validate_group_relationships(
    *,
    program_id: int,
    program_year: ProgramYear,
    specialization: Specialization,
) -> None:
    if program_year.program_id != program_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Program year does not belong to the specified program",
        )
    if specialization.program_id != program_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specialization does not belong to the specified program",
        )


def create_group(
    db: Session,
    *,
    program_id: int,
    program_year_id: int,
    specialization_id: int,
    group_type_code: str,
    code: str,
    actor_user_id: int,
) -> Group:
    program = db.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    program_year = db.get(ProgramYear, program_year_id)
    if not program_year:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program year not found")
    specialization = db.get(Specialization, specialization_id)
    if not specialization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialization not found")
    _validate_group_relationships(
        program_id=program.id,
        program_year=program_year,
        specialization=specialization,
    )
    _ensure_group_type(db, group_type_code)

    group = Group(
        program_id=program_id,
        program_year_id=program_year_id,
        specialization_id=specialization_id,
        group_type_code=group_type_code,
        code=code,
    )
    db.add(group)
    db.flush()
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=Group.__tablename__,
        entity_id=group.id,
        action="create",
        old_data=None,
        new_data=serialize_model(group),
    )
    db.commit()
    db.refresh(group)
    return get_group(db, group.id)


def update_group(
    db: Session,
    group_id: int,
    *,
    program_id: int | None = None,
    program_year_id: int | None = None,
    specialization_id: int | None = None,
    group_type_code: str | None = None,
    code: str | None = None,
    actor_user_id: int,
) -> Group:
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    before = serialize_model(group)

    new_program_id = program_id if program_id is not None else group.program_id
    new_program_year_id = program_year_id if program_year_id is not None else group.program_year_id
    new_specialization_id = (
        specialization_id if specialization_id is not None else group.specialization_id
    )

    program = db.get(Program, new_program_id)
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    program_year = db.get(ProgramYear, new_program_year_id)
    if not program_year:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program year not found")
    specialization = db.get(Specialization, new_specialization_id)
    if not specialization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialization not found")

    _validate_group_relationships(
        program_id=program.id,
        program_year=program_year,
        specialization=specialization,
    )

    if group_type_code is not None:
        _ensure_group_type(db, group_type_code)

    if program_id is not None:
        group.program_id = program_id
    if program_year_id is not None:
        group.program_year_id = program_year_id
    if specialization_id is not None:
        group.specialization_id = specialization_id
    if group_type_code is not None:
        group.group_type_code = group_type_code
    if code is not None:
        group.code = code

    db.flush()
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=Group.__tablename__,
        entity_id=group.id,
        action="update",
        old_data=before,
        new_data=serialize_model(group),
    )
    db.commit()
    db.refresh(group)
    return get_group(db, group.id)


def delete_group(db: Session, group_id: int, *, actor_user_id: int) -> None:
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    before = serialize_model(group)
    _safe_delete(
        db,
        group,
        detail="Group is still in use",
        audit_log={
            "actor_user_id": actor_user_id,
            "entity": Group.__tablename__,
            "entity_id": group.id,
            "action": "delete",
            "old_data": before,
            "new_data": None,
        },
    )
