# Taskflow — Full-Stack Task Management Platform

Taskflow is a role-based task management platform for teams to plan projects, assign work, discuss tasks, and track delivery in one place. It has a React frontend and a FastAPI backend, with MySQL for durable data, Redis for cache and real-time messaging, Celery for background work, and Docker Compose for local development.

> This project is designed as a portfolio-quality backend and full-stack application. The API remains the source of truth for authentication, authorization, validation, and business rules.

## Highlights

- JWT authentication with short-lived access tokens, refresh-token rotation, and logout token revocation
- Role-based access control for **Admins**, **Managers**, and **Developers**
- Teams, memberships, projects, Kanban-style tasks, comments, and task attachments
- Project and task filtering, searching, sorting, and pagination
- Redis-backed caching and rate limiting
- Celery background jobs for task-assignment email notifications
- Real-time notifications with WebSockets and Redis Pub/Sub
- Audit trail for important workspace activity
- Role-scoped dashboard insights
- React + TypeScript frontend with protected routes, notifications, and responsive layouts
- Docker Compose setup for API, frontend, MySQL, Redis, and Celery worker

## Technology stack

| Area | Technology |
| --- | --- |
| Backend API | FastAPI, Python 3.14, Pydantic |
| Database layer | SQLAlchemy 2, Alembic |
| Primary database | MySQL 8.4 |
| Cache / broker | Redis 7 |
| Background jobs | Celery |
| Authentication | JWT (`python-jose`), Passlib/bcrypt |
| Frontend | React 19, TypeScript, Vite |
| Production frontend container | Nginx |
| Local orchestration | Docker Compose |
| Testing | Pytest, FastAPI TestClient |

## Architecture

```text
React + TypeScript frontend (Nginx)
              |
              | HTTP / WebSocket
              v
        FastAPI application
        |        |         |
        |        |         +--> Redis Pub/Sub --> WebSocket notifications
        |        |
        |        +--> Redis cache / rate limits
        |
        +--> MySQL <--> Alembic migrations
        |
        +--> Celery worker --> email notifications
```

## Features by role

| Capability | Admin | Manager | Developer |
| --- | :---: | :---: | :---: |
| Manage application roles | Yes | No | No |
| Create and manage teams/members | Yes | No | No |
| Create and manage projects/tasks in permitted teams | Yes | Yes | No |
| View team projects and tasks | Yes | Managed teams | Member teams |
| Update task status | Yes | Managed teams | Assigned tasks |
| Comment on tasks | Yes | Managed teams | Assigned tasks |
| View audit logs | Yes | No | No |
| View dashboard | Workspace-wide | Managed teams | Member teams |

The backend enforces these rules; the frontend mirrors them to avoid showing actions that will be rejected.

## Quick start with Docker (recommended)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Git

### 1. Clone the project

```bash
git clone <YOUR_REPOSITORY_URL>
cd TaskManagerApp
```

### 2. Create your private environment file

```bash
cp .env.example .env
```

Open `.env` and replace every placeholder. At minimum, set secure values for:

```env
JWT_SECRET_KEY=replace_with_a_long_random_value

MYSQL_DATABASE=task_manager
MYSQL_USER=task_manager_user
MYSQL_PASSWORD=choose_a_development_password
MYSQL_ROOT_PASSWORD=choose_a_different_root_password
```

Generate a JWT secret with:

```bash
openssl rand -hex 32
```

For Docker Compose, this value is a sensible database URL template:

```env
DATABASE_URL=mysql+pymysql://task_manager_user:choose_a_development_password@db:3306/task_manager
```

Docker Compose supplies the correct container-to-container database and Redis URLs to the API and worker at runtime.

### 3. Start the full stack

```bash
docker compose up --build
```

On the first run, Docker will build the Python and React images, start MySQL and Redis, apply Alembic migrations, then start the API, Celery worker, and frontend.

### 4. Open the application

| Service | URL |
| --- | --- |
| Taskflow frontend | <http://localhost:5174> |
| FastAPI Swagger documentation | <http://localhost:8001/docs> |
| FastAPI ReDoc documentation | <http://localhost:8001/redoc> |
| Health endpoint | <http://localhost:8001/health> |

Stop the services with `Ctrl+C`, or from another terminal:

```bash
docker compose down
```

## Useful Docker commands

### View running services

```bash
docker compose ps
```

### Follow a service log

```bash
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f frontend
```

### Open the MySQL terminal

Run this from the project root while the `db` service is running:

```bash
docker compose exec db sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"'
```

Example SQL commands:

```sql
SHOW TABLES;
SELECT id, full_name, email, role FROM users;
exit;
```

### Run Alembic migrations manually

The API applies migrations when started through Compose. To run them manually:

```bash
docker compose exec api alembic upgrade head
```

Create a new migration after changing SQLAlchemy models:

```bash
docker compose run --rm api alembic revision --autogenerate -m "describe_change"
docker compose run --rm api alembic upgrade head
```

## Local development without the API container

Docker Compose is the simplest workflow. If you prefer to run FastAPI directly, still start MySQL and Redis in Docker first:

```bash
docker compose up -d db redis worker
```

Then create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For local Python execution, update your private `.env` to use host-accessible addresses:

```env
DATABASE_URL=mysql+pymysql://task_manager_user:your_password@127.0.0.1:3307/task_manager
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2
```

Apply migrations and start the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

The API is then available at <http://127.0.0.1:8000/docs>.

### Run the frontend in development mode

In a second terminal:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev -- --port 5174
```

The FastAPI application currently allows browser requests from port `5174`, so
keep that port when running Vite locally. When FastAPI runs locally on port
`8000`, set the frontend public variables in `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_WS_URL=ws://127.0.0.1:8000
```

`VITE_*` variables are shipped to the browser. Never place database passwords, JWT secrets, or SMTP credentials in `frontend/.env`.

## Environment variables

The root `.env` is private and must never be committed. `.env.example` is the safe template.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy connection URL. Use `db` as host in Docker, `127.0.0.1:3307` from the host machine. |
| `TEST_DATABASE_URL` | Separate, disposable database used by Pytest. Tests create and drop tables. |
| `JWT_SECRET_KEY` | Secret used to sign JWTs. Generate a long random value. |
| `JWT_ALGORITHM` | JWT signing algorithm; defaults to `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh-token lifetime. |
| `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` | Values used to initialize the MySQL Compose container. |
| `REDIS_URL` | Redis database for cache and real-time messaging. |
| `CACHE_ENABLED`, `CACHE_TTL_SECONDS` | Enables and configures Redis caching. |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Redis URLs used by Celery. |
| `EMAIL_ENABLED` | Enables task-assignment email delivery. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL` | SMTP delivery configuration when email is enabled. |
| `UPLOAD_DIRECTORY`, `MAX_UPLOAD_SIZE_BYTES` | Local task-attachment storage configuration. |
| `RATE_LIMIT_ENABLED`, `RATE_LIMIT_FAIL_OPEN` | Redis-backed API rate-limit behavior. |

## API overview

Interactive OpenAPI documentation is available at `/docs` when the API is running.

| Area | Base route | Examples |
| --- | --- | --- |
| Authentication | `/auth` | register, login, refresh, logout, current profile |
| Teams | `/teams` | create teams, manage memberships, list a user’s teams |
| Projects | `/projects` | create, update, archive, restore, move, search |
| Tasks | `/tasks` | create, assign, update status, role-scoped list, filtering and pagination |
| Comments | `/comments` | create, update, delete, task conversations |
| Attachments | `/attachments` | upload, list, download, delete task files |
| Dashboard | `/dashboard/summary` | role-scoped activity and delivery metrics |
| Notifications | `/notifications` | list and mark notifications as read |
| Audit logs | `/audit-logs` | administrator-only activity history |
| Health | `/health` | database connectivity status |
| WebSocket | `/ws/notifications` | authenticated real-time notification stream |

## Project structure

```text
TaskManagerApp/
├── app/
│   ├── api/              # FastAPI routers and dependencies
│   ├── core/             # Configuration, security, cache, rate limits, Celery
│   ├── db/               # SQLAlchemy session and database models
│   ├── repositories/     # Database query layer
│   ├── schemas/          # Pydantic request/response models
│   ├── services/         # Business rules and authorization
│   ├── realtime/         # Redis Pub/Sub and WebSocket connection handling
│   ├── workers/          # Celery background tasks
│   └── tests/            # Pytest API tests
├── alembic/              # Database migration history
├── frontend/             # React + TypeScript application
├── compose.yaml          # API, frontend, MySQL, Redis, and worker services
├── Dockerfile            # FastAPI container image
├── requirements.txt
└── .env.example
```

## Testing

Create a **separate disposable database** for tests and set it in your private `.env`:

```env
TEST_DATABASE_URL=mysql+pymysql://task_manager_user:your_password@127.0.0.1:3307/task_manager_test
```

> **Warning:** the test setup creates and drops tables in `TEST_DATABASE_URL`. Never point it at your development or production database.

Run backend tests:

```bash
pytest -v
```

Run the frontend production build/type check:

```bash
cd frontend
npm run build
```

## Security notes

- Keep `.env`, database dumps, Redis dumps, and backup files out of Git.
- Rotate a secret immediately if it is ever committed or shared.
- Use strong, unique database and JWT secrets outside local development.
- Do not use wildcard CORS origins with credentialed requests in production.
- Validate authorization in services/endpoints; hiding a frontend button is not a security boundary.

## Planned improvements

- Authorization-aware RAG copilot for permitted project tasks, comments, and documents
- Object storage and virus scanning for production file uploads
- CI pipeline and production deployment configuration
- Improved observability, metrics, and operational health checks

## License

No license has been selected yet. Add a license file before distributing or accepting external contributions.
