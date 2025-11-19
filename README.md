# ab-planner

AB Planner is a FastAPI backend that serves both administrative and student-facing clients.

## Development quickstart

1. **Environment variables**
   ```bash
   cp .env.example .env
   ```
   Adjust the values if you want to override the default Postgres credentials.
2. **Run the stack**
   ```bash
   docker compose up --build
   ```
   The API becomes available on `http://localhost:8000` and Postgres on `localhost:5432`.
3. **Explore the mock API** – Open `http://localhost:8000/docs` to try the endpoints.

## Available mock endpoints

All routes are namespaced under `/api/v1` and return in-memory mock data so the frontend can work before the real repositories are in place.

- `GET /api/v1/users/me` – Current user profile (override with `?user_id=`).
- `GET /api/v1/programs` and `GET /api/v1/programs/{id}/groups` – Academic structures plus groups.
- `GET /api/v1/groups` and `GET /api/v1/groups/{id}` – Group catalog with filtering.
- `GET /api/v1/lessons` – Lesson schedule filtered by group and/or date range.
- `GET /api/v1/notifications` – Notification outbox for a user.
- `GET/POST /api/v1/student-group-selection` – Inspect or stub saving a student’s chosen group.

These responses follow the data model outlined in `.local/app_folder_layout.md` and `.local/db_arhitecture_graph.md` so they can later be backed by real repositories without changing the contract.

## Database models & migrations

- SQLAlchemy models now live under `app/models/` and mirror the ER diagram from `.local/db_arhitecture_graph.md`.
- Alembic is configured in `alembic.ini` with scripts placed in `app/migrations/`.
- To create the schema locally run:
  ```bash
  alembic upgrade head
  ```
  Make sure your `.env` points to a running Postgres instance (Docker Compose supplies one at `db:5432`).
- Generate future migrations with:
  ```bash
  alembic revision --autogenerate -m "describe change"
  ```
