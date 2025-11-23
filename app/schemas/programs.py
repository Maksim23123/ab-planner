from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ProgramYear(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    program_id: int
    year: int


class ProgramYearCreate(BaseModel):
    program_id: int
    year: int


class ProgramYearUpdate(BaseModel):
    program_id: int | None = None
    year: int | None = None


class Specialization(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    program_id: int
    name: str


class SpecializationCreate(BaseModel):
    program_id: int
    name: str


class SpecializationUpdate(BaseModel):
    program_id: int | None = None
    name: str | None = None


class ProgramBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ProgramCreate(BaseModel):
    name: str


class ProgramUpdate(BaseModel):
    name: str | None = None


class Program(ProgramBrief):
    years: list[ProgramYear]
    specializations: list[Specialization]


class GroupType(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    label: str


class Group(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    program: ProgramBrief
    year: ProgramYear
    specialization: Specialization
    group_type: GroupType


class GroupCreate(BaseModel):
    program_id: int
    program_year_id: int
    specialization_id: int
    group_type: str
    code: str


class GroupUpdate(BaseModel):
    program_id: int | None = None
    program_year_id: int | None = None
    specialization_id: int | None = None
    group_type: str | None = None
    code: str | None = None
