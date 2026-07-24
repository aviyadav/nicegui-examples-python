# Order Portal — NiceGUI Internal Business App

A runnable implementation of the operations portal described in
*"Why NiceGUI Is Perfect for Internal Business Apps"*.

NiceGUI owns the whole application while the browser is just a rendering
engine. The backend stays an ordinary, layered Python codebase:

```
UI (nicegui)  ->  Service  ->  Repository  ->  PostgreSQL
                                   |
                                   +-- Redis (cache)  +  Celery (background jobs)
```

## Stack

| Layer        | Tech                                              |
| ------------ | ------------------------------------------------- |
| UI           | NiceGUI (FastAPI + Starlette + Uvicorn + Vue/Quasar + Socket.IO) |
| DB           | PostgreSQL 16 (async SQLAlchemy 2.x + asyncpg)    |
| Cache        | Redis 7 (60s dashboard metrics cache)             |
| Background   | Celery worker (monthly report export)             |
| Auth         | bcrypt + signed session cookie (`itsdangerous`)   |
| Logging      | structlog                                         |

## Quick start

```bash
cd order_portal
docker compose up --build
```

Then open <http://localhost:8080/login>.

The app waits for healthy `db` + `redis`, then auto-creates tables and seeds
demo data on first start (see `app/seed.py`). No Alembic, no manual SQL.

### Demo credentials

| Email                | Password | Role  |
| ------------------- | -------- | ----- |
| `admin@example.com` | `admin`  | admin |
| `ops@example.com`   | `ops`    | user  |

## Routes

| Path       | Description                                                        |
| ---------- | ----------------------------------------------------------------- |
| `/login`   | Email/password login form                                          |
| `/`        | Operations dashboard: revenue + pending cards, orders table, approve |
| `/admin`   | Admin-only user list (non-admins see "Access denied")              |
| `/logout`  | Clears the session and returns to `/login`                         |
| `/health`  | `{status, database, redis}` for orchestrators (PDF p.15)           |

## Features mapped to the article

- **Layered architecture** (`database.py` → `models.py` → `repositories.py` →
  `services.py` → `ui/`) — PDF p.4-7.
- **Dashboard cards** (revenue / pending / count) — PDF p.8.
- **Refreshable orders table** with pagination — PDF p.10-11.
- **One-click Approve** → `ui.notify` + live refresh, no REST/polling — PDF p.9.
- **Redis-cached metrics** (60s TTL) — PDF p.14.
- **Celery background report** + export button — PDF p.12-13.
- **FastAPI `current_user` dependency** reused on `/admin` — PDF p.13.
- **structlog** structured logs — PDF p.15.
- **`/health` endpoint** — PDF p.15.
- **Dockerfile** (PDF p.16) + `docker-compose.yml` for the full stack.

## Project layout

```
order_portal/
├── docker-compose.yml      # db + redis + app + celery-worker
├── Dockerfile              # PDF p.16, python:3.13-slim
├── requirements.txt
├── .env / .env.example
└── app/
    ├── app.py              # entrypoint, /health, startup seed, ui.run()
    ├── database.py         # async engine + get_session()
    ├── models.py           # Order (PDF) + User (auth)
    ├── repositories.py     # OrderRepository + UserRepository
    ├── services.py         # DashboardService, OrderService, ReportService
    ├── auth.py             # login page, session cookie, require_user decorator
    ├── celery_app.py       # generate_monthly_report task
    ├── logging_conf.py     # structlog
    ├── seed.py             # create tables + demo users + 50 sample orders
    └── ui/
        ├── dashboard.py    # @ui.page("/")
        ├── orders.py       # @ui.refreshable orders_table + approve
        └── users.py        # @ui.page("/admin")
```

## Environment

Copy `.env.example` to `.env` and adjust. Defaults work out of the box with
`docker compose`. Notable vars:

- `DATABASE_URL` — overrides `POSTGRES_*` if set.
- `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` — set by compose.
- `SESSION_SECRET` — signs the session cookie. **Change in production.**
- `AUTH_DISABLED=1` — bypass auth for local debugging.

## Notes

- Tables are created via `Base.metadata.create_all` (no Alembic) per the
  "pragmatic extension" choice.
- `reports/` is a bind-mounted volume shared between the `app` and
  `celery-worker` containers, so generated CSVs are visible on the host.
