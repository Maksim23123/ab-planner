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
3. **Explore the API** — Open `http://localhost:8000/docs` to try the endpoints.

## API surface (spec-aligned)

Base path: `/api/v1`  
Headers: `X-User-Id`, `X-User-Role` (`student|lecturer|admin`)

- **Users**
  - `GET /users/me` — current user.
  - `GET /users` (admin), `GET /users/{id}` (admin).
- **Programs** (read for all; admin mutates)
  - `GET /programs`, `GET /programs/{id}`
  - `POST /programs`, `PATCH /programs/{id}`, `DELETE /programs/{id}` (admin)
- **Program Years** (read for all; admin mutates)
  - `GET /program-years`, `GET /program-years/{id}`
  - `POST /program-years`, `PATCH /program-years/{id}`, `DELETE /program-years/{id}` (admin)
- **Specializations** (read for all; admin mutates)
  - `GET /specializations`, `GET /specializations/{id}`
  - `POST /specializations`, `PATCH /specializations/{id}`, `DELETE /specializations/{id}` (admin)
- **Groups** (read for all; admin mutates)
  - `GET /groups` with filters `program_id`, `program_year_id`, `specialization_id`, `group_type`
  - `GET /groups/{id}`, `POST /groups`, `PATCH /groups/{id}`, `DELETE /groups/{id}` (admin)
- **Subjects** (read for all; admin mutates)
  - `GET /subjects`, `GET /subjects/{id}`
  - `POST /subjects`, `PATCH /subjects/{id}`, `DELETE /subjects/{id}` (admin)
- **Rooms** (read for all; admin mutates)
  - `GET /rooms`, `GET /rooms/{id}`
  - `POST /rooms`, `PATCH /rooms/{id}`, `DELETE /rooms/{id}` (admin)
- **Lessons**
  - `GET /lessons` (filters: `group_id`, `date_from`, `date_to`), `GET /lessons/{id}`
  - `POST /lessons` (admin or lecturer-own)
  - `PATCH /lessons/{id}` (scope/field rules by role)
  - `DELETE /lessons/{id}` (admin or lecturer-own)
- **Student Group Selection**
  - `GET /student-group-selection`
  - `PUT /student-group-selection` (student own or admin with `user_id`)
  - `DELETE /student-group-selection` (same access rules)
- **Notifications**
  - `GET /notifications` (own; admin can query any `user_id`; optional `status` filter)
  - `POST /notifications` (admin), `PATCH /notifications/{id}` (owner or admin)

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

## Seeding the database

To load the mock dataset from `app/core/mock_data.py` into Postgres:

```bash
# From the host with your virtualenv active
python -m app.scripts.seed_db

# Or inside the API container
docker compose run --rm api python -m app.scripts.seed_db
```

The script makes sure the database exists, runs Alembic migrations, truncates existing data, and inserts the fixtures with stable IDs to match the mock API responses.
