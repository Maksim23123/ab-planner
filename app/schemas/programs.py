from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ProgramYear(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    program_id: int
    year: int


class Specialization(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    program_id: int
    name: str


class ProgramBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


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
