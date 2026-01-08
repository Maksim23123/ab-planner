from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api import deps
from app.services import plan_service


router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/lecturer", response_class=Response)
def download_lecturer_plan(
    lecturer_user_id: int = Query(..., description="Lecturer user identifier"),
    date_from: date = Query(..., description="Start date (YYYY-MM-DD)"),
    date_to: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    start_at, end_at = plan_service.get_week_window(date_from, date_to)
    lecturer = plan_service.get_lecturer(db, lecturer_user_id)
    lessons = plan_service.list_lecturer_lessons(
        db,
        lecturer_user_id=lecturer_user_id,
        start_at=start_at,
        end_at=end_at,
    )
    pdf_bytes = plan_service.build_lecturer_plan_pdf(
        lecturer,
        lessons,
        date_from=date_from,
        date_to=date_to,
    )
    filename = (
        f"lecturer_{lecturer.id}_plan_{date_from.isoformat()}_{date_to.isoformat()}.pdf"
    )
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
