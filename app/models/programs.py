from __future__ import annotations

from typing import List, TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.lessons import Lesson
    from app.models.selections import StudentGroupSelection


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    years: Mapped[List["ProgramYear"]] = relationship(
        "ProgramYear", back_populates="program", cascade="all, delete-orphan"
    )
    specializations: Mapped[List["Specialization"]] = relationship(
        "Specialization", back_populates="program", cascade="all, delete-orphan"
    )
    groups: Mapped[List["Group"]] = relationship("Group", back_populates="program")


class ProgramYear(Base):
    __tablename__ = "program_years"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    program: Mapped[Program] = relationship("Program", back_populates="years")
    groups: Mapped[List["Group"]] = relationship("Group", back_populates="program_year")


class Specialization(Base):
    __tablename__ = "specializations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    program: Mapped[Program] = relationship("Program", back_populates="specializations")
    groups: Mapped[List["Group"]] = relationship("Group", back_populates="specialization")


class GroupType(Base):
    __tablename__ = "group_types"

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)

    groups: Mapped[List["Group"]] = relationship("Group", back_populates="group_type")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), nullable=False)
    program_year_id: Mapped[int] = mapped_column(ForeignKey("program_years.id"), nullable=False)
    specialization_id: Mapped[int] = mapped_column(ForeignKey("specializations.id"), nullable=False)
    group_type_code: Mapped[str] = mapped_column(
        "group_type", ForeignKey("group_types.code"), nullable=False
    )
    code: Mapped[str] = mapped_column(Text, nullable=False)

    program: Mapped[Program] = relationship("Program", back_populates="groups")
    program_year: Mapped[ProgramYear] = relationship("ProgramYear", back_populates="groups")
    specialization: Mapped[Specialization] = relationship("Specialization", back_populates="groups")
    group_type: Mapped[GroupType] = relationship("GroupType", back_populates="groups")
    lessons: Mapped[List["Lesson"]] = relationship("Lesson", back_populates="group")
    selections: Mapped[List["StudentGroupSelection"]] = relationship(
        "StudentGroupSelection", back_populates="group"
    )

    @property
    def year(self) -> ProgramYear:
        """Alias to keep API schemas using `year` compatible with the ORM relationship."""
        return self.program_year
