from __future__ import annotations

from datetime import datetime, timedelta, timezone


NOW = datetime(2025, 1, 13, 8, 0, tzinfo=timezone.utc)

ROLES = [
    {"id": 1, "code": "student", "label": "Student"},
    {"id": 2, "code": "lecturer", "label": "Lecturer"},
    {"id": 3, "code": "admin", "label": "Administrator"},
]

USERS = [
    {
        "id": 1,
        "email": "anna.student@example.edu",
        "name": "Anna Student",
        "role_id": 1,
        "created_at": NOW - timedelta(days=120),
    },
    {
        "id": 2,
        "email": "dr.igor@example.edu",
        "name": "Dr. Igor Lecturer",
        "role_id": 2,
        "created_at": NOW - timedelta(days=400),
    },
    {
        "id": 3,
        "email": "admin@example.edu",
        "name": "Admin User",
        "role_id": 3,
        "created_at": NOW - timedelta(days=800),
    },
]

PROGRAMS = [
    {"id": 1, "name": "Computer Science"},
    {"id": 2, "name": "Information Systems"},
]

PROGRAM_YEARS = [
    {"id": 1, "program_id": 1, "year": 2025},
    {"id": 2, "program_id": 1, "year": 2024},
    {"id": 3, "program_id": 2, "year": 2025},
]

SPECIALIZATIONS = [
    {"id": 1, "program_id": 1, "name": "AI Engineering"},
    {"id": 2, "program_id": 1, "name": "Cybersecurity"},
    {"id": 3, "program_id": 2, "name": "Business Analytics"},
]

GROUP_TYPES = [
    {"code": "lecture", "label": "Lecture"},
    {"code": "lab", "label": "Laboratory"},
    {"code": "seminar", "label": "Seminar"},
]

GROUPS = [
    {
        "id": 1,
        "program_id": 1,
        "program_year_id": 1,
        "specialization_id": 1,
        "group_type": "lecture",
        "code": "CS-AI-1L",
    },
    {
        "id": 2,
        "program_id": 1,
        "program_year_id": 1,
        "specialization_id": 1,
        "group_type": "lab",
        "code": "CS-AI-1LAB",
    },
    {
        "id": 3,
        "program_id": 1,
        "program_year_id": 1,
        "specialization_id": 2,
        "group_type": "lecture",
        "code": "CS-CY-1L",
    },
]

SUBJECTS = [
    {"id": 1, "name": "Distributed Systems", "code": "CS201"},
    {"id": 2, "name": "Machine Learning", "code": "CS305"},
]

ROOMS = [
    {"id": 1, "number": "A101", "building": "Main", "capacity": 100},
    {"id": 2, "number": "Lab-3", "building": "Innovation", "capacity": 24},
]

LESSONS = [
    {
        "id": 1,
        "subject_id": 1,
        "lecturer_user_id": 2,
        "room_id": 1,
        "group_id": 1,
        "starts_at": NOW.replace(hour=8, minute=0),
        "ends_at": NOW.replace(hour=9, minute=30),
        "status": "scheduled",
        "lesson_type": "lecture",
    },
    {
        "id": 2,
        "subject_id": 2,
        "lecturer_user_id": 2,
        "room_id": 2,
        "group_id": 2,
        "starts_at": NOW.replace(day=NOW.day + 1, hour=10, minute=0),
        "ends_at": NOW.replace(day=NOW.day + 1, hour=12, minute=0),
        "status": "rescheduled",
        "lesson_type": "lab",
    },
]

NOTIFICATIONS = [
    {
        "id": 1,
        "user_id": 1,
        "payload": {
            "title": "Lesson moved",
            "body": "Machine Learning lab moved to tomorrow 10:00",
        },
        "delivery_status": "queued",
        "read_status": "unread",
        "read_at": None,
        "last_error": None,
        "attempts": 0,
        "created_at": NOW - timedelta(hours=5),
        "last_attempt_at": None,
        "sent_at": None,
    },
    {
        "id": 2,
        "user_id": 1,
        "payload": {
            "title": "New announcement",
            "body": "Distributed Systems lecture confirmed",
        },
        "delivery_status": "sent",
        "read_status": "read",
        "read_at": NOW - timedelta(hours=18),
        "last_error": None,
        "attempts": 1,
        "created_at": NOW - timedelta(days=1),
        "last_attempt_at": NOW - timedelta(hours=20),
        "sent_at": NOW - timedelta(hours=20),
    },
]

STUDENT_SELECTIONS = [
    {
        "id": 1,
        "user_id": 1,
        "group_id": 2,
        "selected_at": NOW - timedelta(days=7),
    }
]
