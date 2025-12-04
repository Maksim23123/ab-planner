# Bash command to run: python -m app.scripts.seed_db
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core import mock_data
from app.core.database import SessionLocal, ensure_database
from app.core.run_migrations import ensure_schema_up_to_date
from app.models import (
    AuthSession,
    ChangeLog,
    Group,
    GroupType,
    Lesson,
    NotificationOutbox,
    Program,
    ProgramYear,
    Role,
    Room,
    Specialization,
    StudentGroupSelection,
    Subject,
    User,
)


def _truncate_tables(session: Session) -> None:
    """Remove existing data so seeding is repeatable."""
    session.execute(
            text(
                "TRUNCATE TABLE "
                "student_group_selection, notification_outbox, lessons, groups, group_types, "
                "rooms, subjects, specializations, program_years, programs, fcm_tokens, "
                "lecturer_profiles, change_logs, auth_sessions, users, roles "
                "RESTART IDENTITY CASCADE"
            )
        )


def _sync_sequences(session: Session, tables: Iterable[str]) -> None:
    """Advance serial sequences to the current max(id) so future inserts do not collide."""
    for table in tables:
        max_id = session.scalar(text(f"SELECT MAX(id) FROM {table}"))
        if max_id is None:
            session.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), 1, false)"
                )
            )
        else:
            session.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), :val)"
                ),
                {"val": max_id},
            )


def seed() -> None:
    """Populate the database with the mock data set."""
    ensure_database()
    ensure_schema_up_to_date()

    with SessionLocal() as session:
        with session.begin():
            _truncate_tables(session)

            session.add_all([Role(**payload) for payload in mock_data.ROLES])
            session.add_all([User(**payload) for payload in mock_data.USERS])
            session.add_all([Program(**payload) for payload in mock_data.PROGRAMS])
            session.add_all([ProgramYear(**payload) for payload in mock_data.PROGRAM_YEARS])
            session.add_all([Specialization(**payload) for payload in mock_data.SPECIALIZATIONS])
            session.add_all([GroupType(**payload) for payload in mock_data.GROUP_TYPES])

            session.add_all(
                [
                    Group(
                        id=payload["id"],
                        program_id=payload["program_id"],
                        program_year_id=payload["program_year_id"],
                        specialization_id=payload["specialization_id"],
                        group_type_code=payload["group_type"],
                        code=payload["code"],
                    )
                    for payload in mock_data.GROUPS
                ]
            )

            session.add_all([Subject(**payload) for payload in mock_data.SUBJECTS])
            session.add_all([Room(**payload) for payload in mock_data.ROOMS])

            session.add_all(
                [
                    Lesson(
                        id=payload["id"],
                        subject_id=payload["subject_id"],
                        lecturer_user_id=payload["lecturer_user_id"],
                        room_id=payload["room_id"],
                        group_id=payload["group_id"],
                        starts_at=payload["starts_at"],
                        ends_at=payload["ends_at"],
                        status=payload["status"],
                        lesson_type=payload["lesson_type"],
                    )
                    for payload in mock_data.LESSONS
                ]
            )

            session.add_all(
                [
                    NotificationOutbox(
                        id=payload["id"],
                        user_id=payload["user_id"],
                        payload=payload["payload"],
                        delivery_status=payload["delivery_status"],
                        read_status=payload["read_status"],
                        read_at=payload.get("read_at"),
                        last_error=payload.get("last_error"),
                        attempts=payload["attempts"],
                        created_at=payload["created_at"],
                        last_attempt_at=payload.get("last_attempt_at"),
                        sent_at=payload["sent_at"],
                    )
                    for payload in mock_data.NOTIFICATIONS
                ]
            )

            session.add_all(
                [
                    StudentGroupSelection(
                        id=payload["id"],
                        user_id=payload["user_id"],
                        group_id=payload["group_id"],
                        selected_at=payload["selected_at"],
                    )
                    for payload in mock_data.STUDENT_SELECTIONS
                ]
            )

            # Add a few historical change logs to validate pruning/retention.
            seed_now = datetime.now(timezone.utc)

            session.add_all(
                [
                    ChangeLog(
                        actor_user_id=1,
                        entity="programs",
                        entity_id=1,
                        action="update",
                        old_data={"name": "Old CS"},
                        new_data={"name": "Computer Science"},
                        created_at=mock_data.NOW - timedelta(days=120),
                    ),
                    ChangeLog(
                        actor_user_id=2,
                        entity="lessons",
                        entity_id=1,
                        action="update",
                        old_data={"status": "scheduled"},
                        new_data={"status": "rescheduled"},
                        created_at=mock_data.NOW - timedelta(days=45),
                    ),
                    ChangeLog(
                        actor_user_id=3,
                        entity="groups",
                        entity_id=1,
                        action="delete",
                        old_data={"code": "CS-AI-OLD"},
                        new_data=None,
                        created_at=mock_data.NOW - timedelta(days=5),
                    ),
                    # Fresh entries that should survive pruning windows by default.
                    ChangeLog(
                        actor_user_id=1,
                        entity="subjects",
                        entity_id=2,
                        action="update",
                        old_data={"name": "ML"},
                        new_data={"name": "Machine Learning Advanced"},
                        created_at=seed_now - timedelta(days=10),
                    ),
                    ChangeLog(
                        actor_user_id=2,
                        entity="rooms",
                        entity_id=1,
                        action="create",
                        old_data=None,
                        new_data={"number": "A101", "building": "Main", "capacity": 100},
                        created_at=seed_now - timedelta(days=1),
                    ),
                ]
            )

            now = datetime.now(timezone.utc)
            session.add_all(
                [
                    AuthSession(
                        id=1,
                        user_id=1,
                        token_hash="expired_revoked_hash",
                        jti="expired-revoked-jti",
                        created_at=now - timedelta(days=20),
                        expires_at=now - timedelta(days=10),
                        revoked_at=now - timedelta(days=9),
                        revoked_reason="seed expired revoked",
                    ),
                    AuthSession(
                        id=2,
                        user_id=1,
                        token_hash="expired_active_hash",
                        jti="expired-active-jti",
                        created_at=now - timedelta(days=5),
                        expires_at=now - timedelta(days=1),
                        revoked_at=None,
                        revoked_reason=None,
                    ),
                    AuthSession(
                        id=3,
                        user_id=2,
                        token_hash="valid_hash",
                        jti="valid-jti",
                        created_at=now - timedelta(days=1),
                        expires_at=now + timedelta(days=6),
                        revoked_at=None,
                        revoked_reason=None,
                    ),
                ]
            )

            session.flush()  # ensure inserts are written before sequence sync
            _sync_sequences(
                session,
                [
                    "roles",
                    "users",
                    "auth_sessions",
                    "programs",
                    "program_years",
                    "specializations",
                    "groups",
                    "subjects",
                    "rooms",
                    "lessons",
                    "notification_outbox",
                    "student_group_selection",
                    "fcm_tokens",
                    "lecturer_profiles",
                    "change_logs",
                ],
            )

    print("Database seeded with mock data.")


if __name__ == "__main__":
    seed()
