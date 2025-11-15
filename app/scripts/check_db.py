from sqlalchemy import text
from app.core.database import SessionLocal

def check_db() -> None:
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
        print("Database connection OK")


if __name__ == "__main__":
    check_db()