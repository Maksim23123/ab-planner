from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.core import mock_data
from app.core.config import get_settings


ROLE_BY_ID = {role["id"]: role for role in mock_data.ROLES}
USER_BY_ID = {user["id"]: user for user in mock_data.USERS}
PROGRAM_BY_ID = {program["id"]: program for program in mock_data.PROGRAMS}
PROGRAM_YEAR_BY_ID = {item["id"]: item for item in mock_data.PROGRAM_YEARS}
SPECIALIZATION_BY_ID = {item["id"]: item for item in mock_data.SPECIALIZATIONS}
GROUP_TYPE_BY_CODE = {item["code"]: item for item in mock_data.GROUP_TYPES}
GROUP_BY_ID = {group["id"]: group for group in mock_data.GROUPS}
SUBJECT_BY_ID = {subject["id"]: subject for subject in mock_data.SUBJECTS}
ROOM_BY_ID = {room["id"]: room for room in mock_data.ROOMS}


def _role(role_id: int) -> Dict[str, Any]:
    return ROLE_BY_ID[role_id]


def _user_summary(user_id: int) -> Dict[str, Any]:
    user = USER_BY_ID[user_id]
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


def _group_type(code: str) -> Dict[str, Any]:
    return GROUP_TYPE_BY_CODE[code]


def _program(program_id: int) -> Dict[str, Any]:
    return PROGRAM_BY_ID[program_id]


def _program_year(program_year_id: int) -> Dict[str, Any]:
    return PROGRAM_YEAR_BY_ID[program_year_id]


def _specialization(spec_id: int) -> Dict[str, Any]:
    return SPECIALIZATION_BY_ID[spec_id]


def _group_payload(group: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": group["id"],
        "code": group["code"],
        "program": _program(group["program_id"]),
        "year": _program_year(group["program_year_id"]),
        "specialization": _specialization(group["specialization_id"]),
        "group_type": _group_type(group["group_type"]),
    }


def get_user(user_id: Optional[int] = None) -> Dict[str, Any]:
    settings = get_settings()
    target_id = user_id or settings.default_user_id
    user = USER_BY_ID.get(target_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    payload = {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "created_at": user["created_at"],
        "role": _role(user["role_id"]),
    }
    return payload


def list_programs() -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    for program in mock_data.PROGRAMS:
        program_years = [item for item in mock_data.PROGRAM_YEARS if item["program_id"] == program["id"]]
        specializations = [item for item in mock_data.SPECIALIZATIONS if item["program_id"] == program["id"]]
        data.append({
            "id": program["id"],
            "name": program["name"],
            "years": program_years,
            "specializations": specializations,
        })
    return data


def list_groups(
    program_id: Optional[int] = None,
    program_year_id: Optional[int] = None,
    specialization_id: Optional[int] = None,
    group_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    groups = mock_data.GROUPS
    if program_id is not None:
        groups = [g for g in groups if g["program_id"] == program_id]
    if program_year_id is not None:
        groups = [g for g in groups if g["program_year_id"] == program_year_id]
    if specialization_id is not None:
        groups = [g for g in groups if g["specialization_id"] == specialization_id]
    if group_type is not None:
        groups = [g for g in groups if g["group_type"] == group_type]
    return [_group_payload(group) for group in groups]


def get_group(group_id: int) -> Dict[str, Any]:
    group = GROUP_BY_ID.get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return _group_payload(group)


def list_lessons(
    *,
    group_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    lessons = mock_data.LESSONS
    if group_id is not None:
        lessons = [lesson for lesson in lessons if lesson["group_id"] == group_id]
    if date_from is not None:
        lessons = [lesson for lesson in lessons if lesson["starts_at"] >= date_from]
    if date_to is not None:
        lessons = [lesson for lesson in lessons if lesson["starts_at"] <= date_to]

    payloads: List[Dict[str, Any]] = []
    for lesson in lessons:
        payloads.append(
            {
                "id": lesson["id"],
                "starts_at": lesson["starts_at"],
                "ends_at": lesson["ends_at"],
                "status": lesson["status"],
                "lesson_type": lesson["lesson_type"],
                "subject": SUBJECT_BY_ID[lesson["subject_id"]],
                "room": ROOM_BY_ID[lesson["room_id"]],
                "group": _group_payload(GROUP_BY_ID[lesson["group_id"]]),
                "lecturer": _user_summary(lesson["lecturer_user_id"]),
            }
        )
    return payloads


def list_notifications(user_id: Optional[int] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    settings = get_settings()
    target_id = user_id or settings.default_user_id
    notifications = [item for item in mock_data.NOTIFICATIONS if item["user_id"] == target_id]
    if status:
        notifications = [item for item in notifications if item["status"] == status]
    return notifications


def create_group_selection(group_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
    settings = get_settings()
    target_id = user_id or settings.default_user_id
    if group_id not in GROUP_BY_ID:
        raise HTTPException(status_code=404, detail="Group not found")

    new_id = max((item["id"] for item in mock_data.STUDENT_SELECTIONS), default=0) + 1
    record = {
        "id": new_id,
        "user_id": target_id,
        "group_id": group_id,
        "selected_at": datetime.now(tz=timezone.utc),
    }
    mock_data.STUDENT_SELECTIONS.append(record)
    return record


def list_group_selections(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    settings = get_settings()
    target_id = user_id or settings.default_user_id
    return [item for item in mock_data.STUDENT_SELECTIONS if item["user_id"] == target_id]
