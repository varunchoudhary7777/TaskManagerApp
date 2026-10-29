# Taskflow frontend

This is the React + TypeScript frontend for the FastAPI Task Manager API. It is intentionally a separate application: the browser interface owns presentation and user interaction; FastAPI remains the source of truth for authentication, permissions, business rules, MySQL, Redis, Celery, and WebSockets.

## What the interface supports

| Frontend area | FastAPI features used |
| --- | --- |
| Sign in and account creation | registration, JWT access tokens, refresh-token rotation, logout |
| Overview | dashboard summary, recent projects, current tasks, health check |
| Projects | create, edit, status changes, archive/restore, delete, search, filtering, sorting and pagination |
| Tasks | Kanban board, task creation/editing, status updates, assignment, Celery assignment-email trigger |
| Task detail | comments, file uploads, downloads, file deletion, task status and assignment |
| Teams | create/update/delete teams, list/add/remove team members |
| Notifications | persisted notification inbox, mark-as-read action, live WebSocket updates from Redis Pub/Sub |
| Admin | audit log viewer and application role changes |
| Settings | authenticated profile and `/health` status |

Rate-limit, validation, and authorization errors are shown as application messages. Redis caching, MySQL, Celery and audit logging continue to run in the backend: they do not need a dedicated button in the browser.

## Run locally

Open a second terminal in this `frontend` directory:

```bash
cp .env.example .env
npm install
npm run dev
```

Open <http://127.0.0.1:5173>.

The FastAPI API must already be running at `http://127.0.0.1:8000`. When using Docker Compose:

```bash
docker compose up --build
```

Run that command in the project root, not in this `frontend` directory.

With the new `frontend` Docker Compose service, the same command also serves the
production frontend at <http://127.0.0.1:5173>. It is served by Nginx while the
browser still calls FastAPI at <http://127.0.0.1:8000>.

## Backend integration added for the browser

The project now has CORS middleware configured from `FRONTEND_ORIGINS`. Its development default is:

```env
FRONTEND_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

If you have an existing root `.env`, add this line to it. Do not replace the file or place any secrets in `frontend/.env`.

The `TaskResponse` schema was expanded to return `status`, `priority`, and `due_date`. This is necessary because an accurate Kanban board cannot be built if the API hides those fields.

## Environment variables

`frontend/.env` contains only public browser configuration:

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_WS_URL=ws://127.0.0.1:8000
```

Never put `JWT_SECRET_KEY`, database passwords, SMTP credentials, or Redis credentials in frontend environment variables. Anything beginning with `VITE_` is included in browser-delivered JavaScript.

## Production build

```bash
npm run build
```

This creates `frontend/dist/`. Serve those static files through a frontend host such as Vercel, Netlify, Cloudflare Pages, or Nginx. Update both `VITE_API_URL` and `VITE_WS_URL` at build time, then set the deployed frontend URL in the backend's `FRONTEND_ORIGINS` value.
