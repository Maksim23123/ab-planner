# ab-planner

AB Planner is a FastAPI backend that serves both administrative and student-facing clients.

## Development quickstart

1. **Environment variables**
   ```bash
   cp .env.example .env
   ```
   Adjust the values for Postgres *and* provide the Microsoft OAuth credentials (`MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `MS_TENANT`, `MS_REDIRECT_URI`, scopes) plus the auth token settings (`AUTH_SECRET_KEY`, TTLs, default role). These power the login endpoints described below.
2. **Run the stack**
   ```bash
   docker compose up --build
   ```
   The API becomes available on `http://localhost:8000` and Postgres on `localhost:5432`.
3. **Explore the API** — Open `http://localhost:8000/docs` to try the endpoints.

## API surface (spec-aligned)

Base path: `/api/v1`  
Headers: `Authorization: Bearer <access_token>`

### Authentication flow

1. The front-end initiates the Microsoft OAuth 2.0 authorization code flow (PKCE) and, after the user signs in, receives a `{ code, code_verifier }` pair. You can construct the authorize URL yourself or call `GET /api/v1/auth/microsoft/login-url?code_challenge=<value>` to have the API generate a Microsoft login link that already contains the correct tenant/client/scope parameters; keep the PKCE `code_verifier` so you can complete the exchange.
2. Call `POST /api/v1/auth/microsoft/token` with `{ code, code_verifier, redirect_uri }`. The backend exchanges the code with Microsoft, links/creates a user by email, and returns `{ access_token, refresh_token, expires_in, user }`.
3. Include the access token from the response in the `Authorization` header when calling any protected endpoint.
4. When the access token expires, call `POST /api/v1/auth/refresh` with `{ refresh_token }` to obtain a fresh pair of tokens.

- **Users**
  - `GET /users/me` — current user.
  - `GET /users` (admin), `GET /users/{id}` (admin).
- **Auth**
  - `GET /auth/microsoft/login-url` — helper that returns the Microsoft authorize URL for a given PKCE `code_challenge` (optional `state`).
  - `POST /auth/microsoft/token` — exchange Microsoft authorization code for AB Planner tokens.
  - `POST /auth/refresh` — rotate tokens using a refresh token.
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
  - `POST /lessons/series` (admin or lecturer-own) — create a recurring set of lessons by providing the base lesson, interval in days, and number of occurrences
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

To seed only the reference data the API requires (roles, group types, and a default admin user), without wiping existing records:

```bash
# Optionally override the admin user that will be ensured
$env:ADMIN_EMAIL="admin@example.edu"
$env:ADMIN_NAME="Admin User"
# Decide whether to create/update an admin user (default: false)
$env:SEED_ADMIN="true"

# From the host with your virtualenv active
python -m app.scripts.seed_minimal_db

# Or inside the API container
docker compose run --rm `
  -e ADMIN_EMAIL=$env:ADMIN_EMAIL `
  -e ADMIN_NAME=$env:ADMIN_NAME `
  -e SEED_ADMIN=$env:SEED_ADMIN `
  api python -m app.scripts.seed_minimal_db
```

To load the full mock dataset from `app/core/mock_data.py` into Postgres:

```bash
# From the host with your virtualenv active
python -m app.scripts.seed_db

# Or inside the API container
docker compose run --rm api python -m app.scripts.seed_db
```

Both scripts ensure the database exists and run Alembic migrations. The minimal seeder leaves existing data intact, while the full seeder truncates tables and inserts the fixtures with stable IDs to match the mock API responses.
