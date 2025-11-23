from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Group, Program, ProgramYear, Specialization, GroupType


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


def get_program(db: Session, program_id: int) -> Program:
    stmt = (
        select(Program)
        .options(
            joinedload(Program.years),
            joinedload(Program.specializations),
        )
        .where(Program.id == program_id)
    )
    program = db.execute(stmt).scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    return program


def create_program(db: Session, name: str) -> Program:
    program = Program(name=name)
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


def update_program(db: Session, program_id: int, *, name: str | None = None) -> Program:
    program = db.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    if name is not None:
        program.name = name
    db.commit()
    db.refresh(program)
    return get_program(db, program.id)


def delete_program(db: Session, program_id: int) -> None:
    program = db.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    db.delete(program)
    db.commit()


def list_program_years(db: Session) -> list[ProgramYear]:
    stmt = select(ProgramYear).options(joinedload(ProgramYear.program)).order_by(ProgramYear.id)
    return list(db.scalars(stmt).all())


def get_program_year(db: Session, year_id: int) -> ProgramYear:
    stmt = select(ProgramYear).options(joinedload(ProgramYear.program)).where(ProgramYear.id == year_id)
    program_year = db.execute(stmt).scalar_one_or_none()
    if not program_year:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program year not found")
    return program_year


def create_program_year(db: Session, program_id: int, year: int) -> ProgramYear:
    if db.get(Program, program_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    record = ProgramYear(program_id=program_id, year=year)
    db.add(record)
    db.commit()
    db.refresh(record)
    return get_program_year(db, record.id)


def update_program_year(db: Session, year_id: int, *, year: int | None = None, program_id: int | None = None) -> ProgramYear:
    record = db.get(ProgramYear, year_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program year not found")
    if program_id is not None and db.get(Program, program_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    if program_id is not None:
        record.program_id = program_id
    if year is not None:
        record.year = year
    db.commit()
    db.refresh(record)
    return get_program_year(db, record.id)


def delete_program_year(db: Session, year_id: int) -> None:
    record = db.get(ProgramYear, year_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program year not found")
    db.delete(record)
    db.commit()


def list_specializations(db: Session) -> list[Specialization]:
    stmt = select(Specialization).options(joinedload(Specialization.program)).order_by(Specialization.id)
    return list(db.scalars(stmt).all())


def get_specialization(db: Session, spec_id: int) -> Specialization:
    stmt = select(Specialization).options(joinedload(Specialization.program)).where(Specialization.id == spec_id)
    spec = db.execute(stmt).scalar_one_or_none()
    if not spec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialization not found")
    return spec


def create_specialization(db: Session, program_id: int, name: str) -> Specialization:
    if db.get(Program, program_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    spec = Specialization(program_id=program_id, name=name)
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return get_specialization(db, spec.id)


def update_specialization(
    db: Session,
    spec_id: int,
    *,
    name: str | None = None,
    program_id: int | None = None,
) -> Specialization:
    spec = db.get(Specialization, spec_id)
    if not spec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialization not found")
    if program_id is not None and db.get(Program, program_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    if program_id is not None:
        spec.program_id = program_id
    if name is not None:
        spec.name = name
    db.commit()
    db.refresh(spec)
    return get_specialization(db, spec.id)


def delete_specialization(db: Session, spec_id: int) -> None:
    spec = db.get(Specialization, spec_id)
    if not spec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialization not found")
    db.delete(spec)
    db.commit()


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


def _ensure_group_type(db: Session, code: str) -> None:
    if db.get(GroupType, code) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group type not found")


def create_group(
    db: Session,
    *,
    program_id: int,
    program_year_id: int,
    specialization_id: int,
    group_type_code: str,
    code: str,
) -> Group:
    if db.get(Program, program_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    if db.get(ProgramYear, program_year_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program year not found")
    if db.get(Specialization, specialization_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialization not found")
    _ensure_group_type(db, group_type_code)

    group = Group(
        program_id=program_id,
        program_year_id=program_year_id,
        specialization_id=specialization_id,
        group_type_code=group_type_code,
        code=code,
    )
    db.add(group)
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
) -> Group:
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if program_id is not None and db.get(Program, program_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    if program_year_id is not None and db.get(ProgramYear, program_year_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program year not found")
    if specialization_id is not None and db.get(Specialization, specialization_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialization not found")
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

    db.commit()
    db.refresh(group)
    return get_group(db, group.id)


def delete_group(db: Session, group_id: int) -> None:
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    db.delete(group)
    db.commit()
