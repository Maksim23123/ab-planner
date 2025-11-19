from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.database import TARGET_URL


def ensure_schema_up_to_date() -> None:
    cfg = Config(str(Path(__file__).resolve().parent.parent.parent / "alembic.ini"))
    cfg.set_main_option(
        "sqlalchemy.url", TARGET_URL.render_as_string(hide_password=False)
    )
    command.upgrade(cfg, "head")
