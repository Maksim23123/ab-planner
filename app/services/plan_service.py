from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from io import BytesIO
import os
from pathlib import Path
from typing import Sequence

from fastapi import HTTPException, status
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lesson, User
from app.services.lesson_service import _with_relations


_FONT_NAME: str | None = None


def get_week_window(date_from: date, date_to: date) -> tuple[datetime, datetime]:
    if date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_to must be on or after date_from",
        )
    span_days = (date_to - date_from).days + 1
    if span_days != 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date range must cover exactly 7 days",
        )

    start_at = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
    end_at = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return start_at, end_at


def get_lecturer(db: Session, lecturer_user_id: int) -> User:
    lecturer = db.get(User, lecturer_user_id)
    if not lecturer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecturer not found")
    role_code = (getattr(lecturer.role, "code", "") or "").lower()
    if role_code != "lecturer":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecturer not found")
    return lecturer


def list_lecturer_lessons(
    db: Session,
    *,
    lecturer_user_id: int,
    start_at: datetime,
    end_at: datetime,
) -> list[Lesson]:
    stmt = (
        select(Lesson)
        .options(*_with_relations())
        .where(
            Lesson.lecturer_user_id == lecturer_user_id,
            Lesson.starts_at >= start_at,
            Lesson.starts_at < end_at,
        )
        .order_by(Lesson.starts_at, Lesson.id)
    )
    return list(db.scalars(stmt).all())


def build_lecturer_plan_pdf(
    lecturer: User,
    lessons: Sequence[Lesson],
    *,
    date_from: date,
    date_to: date,
) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    font_name = _resolve_pdf_font()
    y = height - margin

    pdf.setTitle("Lecturer Plan")
    pdf.setAuthor("AB Planner")

    def draw_wrapped(text: str, *, font_size: int, indent: int = 0, extra_space: int = 0) -> None:
        nonlocal y
        max_width = width - (margin * 2) - indent
        lines = _wrap_text(text, font_name, font_size, max_width)
        line_height = int(font_size * 1.3)
        for line in lines:
            if y - line_height < margin:
                pdf.showPage()
                y = height - margin
            pdf.setFont(font_name, font_size)
            pdf.drawString(margin + indent, y, line)
            y -= line_height
        y -= extra_space

    draw_wrapped("Lecturer plan", font_size=16, extra_space=6)
    draw_wrapped(
        f"Lecturer: {lecturer.name} ({lecturer.email})",
        font_size=11,
    )
    draw_wrapped(
        f"Week: {date_from.isoformat()} to {date_to.isoformat()}",
        font_size=11,
        extra_space=10,
    )

    if not lessons:
        draw_wrapped("No lessons scheduled for this week.", font_size=11)
        pdf.save()
        buffer.seek(0)
        return buffer.getvalue()

    lessons_by_day: dict[date, list[Lesson]] = defaultdict(list)
    for lesson in lessons:
        day = lesson.starts_at.date()
        lessons_by_day[day].append(lesson)

    for day in sorted(lessons_by_day):
        day_title = day.strftime("%A, %Y-%m-%d")
        draw_wrapped(day_title, font_size=12, extra_space=4)
        for lesson in lessons_by_day[day]:
            time_window = f"{lesson.starts_at:%H:%M}-{lesson.ends_at:%H:%M}"
            subject = lesson.subject.name if lesson.subject else "Lesson"
            lesson_type = lesson.lesson_type or "lesson"
            draw_wrapped(
                f"{time_window}  {subject} ({lesson_type})",
                font_size=11,
                indent=12,
            )
            group_label = _format_group(lesson)
            room_label = _format_room(lesson)
            status_label = lesson.status or "scheduled"
            draw_wrapped(
                f"{group_label} | {room_label} | Status: {status_label}",
                font_size=10,
                indent=24,
                extra_space=4,
            )

        y -= 2

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def _wrap_text(text: str, font_name: str, font_size: int, max_width: float) -> list[str]:
    if font_name == "Helvetica":
        text = text.encode("latin-1", "replace").decode("latin-1")
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _resolve_pdf_font() -> str:
    global _FONT_NAME
    if _FONT_NAME is not None:
        return _FONT_NAME

    windows_dir = Path(os.environ.get("WINDIR", "C:\\Windows"))
    candidates: list[Path] = [
        windows_dir / "Fonts" / "arial.ttf",
        windows_dir / "Fonts" / "calibri.ttf",
        windows_dir / "Fonts" / "segoeui.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ]

    for path in candidates:
        if not path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("PlanFont", str(path)))
        except Exception:
            continue
        _FONT_NAME = "PlanFont"
        return _FONT_NAME

    _FONT_NAME = "Helvetica"
    return _FONT_NAME


def _format_group(lesson: Lesson) -> str:
    if not lesson.group:
        return "Group: TBD"
    code = lesson.group.code or "Group"
    label = ""
    if lesson.group.group_type and lesson.group.group_type.label:
        label = lesson.group.group_type.label
    if label:
        return f"Group: {code} ({label})"
    return f"Group: {code}"


def _format_room(lesson: Lesson) -> str:
    if not lesson.room:
        return "Room: TBD"
    building = lesson.room.building or ""
    number = lesson.room.number or ""
    if building and number:
        return f"Room: {building} {number}"
    if number:
        return f"Room: {number}"
    return "Room: TBD"
