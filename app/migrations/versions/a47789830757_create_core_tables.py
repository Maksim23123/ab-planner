"""create core tables

Revision ID: a47789830757
Revises: 
Create Date: 2025-11-16 18:32:25.168618

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a47789830757'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "roles",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )

    op.create_table(
        "programs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
    )

    op.create_table(
        "group_types",
        sa.Column("code", sa.Text(), primary_key=True),
        sa.Column("label", sa.Text(), nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "program_years",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("program_id", sa.BigInteger(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"]),
        sa.UniqueConstraint("program_id", "year", name="uq_program_years_program_year"),
    )

    op.create_table(
        "specializations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("program_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"]),
        sa.UniqueConstraint("program_id", "name", name="uq_specializations_program_name"),
    )

    op.create_table(
        "fcm_tokens",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token", sa.Text(), nullable=False),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    op.create_table(
        "lecturer_profiles",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id", name="uq_lecturer_profiles_user"),
    )

    op.create_table(
        "change_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=False),
        sa.Column("entity", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("old_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
    )

    op.create_table(
        "subjects",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.UniqueConstraint("code", name="uq_subjects_code"),
    )

    op.create_table(
        "rooms",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("number", sa.Text(), nullable=False),
        sa.Column("building", sa.Text(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
    )

    op.create_table(
        "groups",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("program_id", sa.BigInteger(), nullable=False),
        sa.Column("program_year_id", sa.BigInteger(), nullable=False),
        sa.Column("specialization_id", sa.BigInteger(), nullable=False),
        sa.Column("group_type", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"]),
        sa.ForeignKeyConstraint(["program_year_id"], ["program_years.id"]),
        sa.ForeignKeyConstraint(["specialization_id"], ["specializations.id"]),
        sa.ForeignKeyConstraint(["group_type"], ["group_types.code"]),
        sa.UniqueConstraint("code", name="uq_groups_code"),
    )

    op.create_table(
        "lessons",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("subject_id", sa.BigInteger(), nullable=False),
        sa.Column("lecturer_user_id", sa.BigInteger(), nullable=False),
        sa.Column("room_id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("lesson_type", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["lecturer_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
    )

    op.create_table(
        "notification_outbox",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    op.create_table(
        "student_group_selection",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.UniqueConstraint("user_id", "group_id", name="uq_selection_user_group"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("student_group_selection")
    op.drop_table("notification_outbox")
    op.drop_table("lessons")
    op.drop_table("groups")
    op.drop_table("rooms")
    op.drop_table("subjects")
    op.drop_table("change_logs")
    op.drop_table("lecturer_profiles")
    op.drop_table("fcm_tokens")
    op.drop_table("specializations")
    op.drop_table("program_years")
    op.drop_table("users")
    op.drop_table("group_types")
    op.drop_table("programs")
    op.drop_table("roles")
