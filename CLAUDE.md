# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Youtharoot is a youth group management platform for tracking events, attendance, and people. It has a **FastAPI backend** and an **Astro + React frontend**, deployed on Railway (backend) and Vercel (frontend).

## Commands

### Backend

```bash
# Activate virtual environment (always required first)
source venv/bin/activate

# Start backend dev server (from repo root)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# or from backend/ directory:
cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run all backend tests
cd backend && python -m pytest tests/ -v

# Run a single test file
cd backend && python -m pytest tests/test_backend_admin_security.py -v

# Run with coverage
cd backend && python -m pytest tests/ --cov=app --cov-report=html
```

### Frontend

```bash
# Start frontend dev server (from frontend/ directory)
cd frontend && npm run dev
# Runs at http://localhost:4321

# Run frontend tests (watch mode)
cd frontend && npm test

# Run frontend tests once
cd frontend && npm run test:run

# Build for production
cd frontend && npm run build
```

## Architecture

### Backend (`backend/`)

- **`app/main.py`** — FastAPI app, CORS setup, router registration, lifespan startup
- **`app/config.py`** — Settings loaded from env vars; controls `DATABASE_TYPE` (`memory` | `postgresql`)
- **`app/database.py`** — SQLAlchemy engine and session management
- **`app/models.py`** — Pydantic models (API request/response shapes)
- **`app/db_models.py`** — SQLAlchemy ORM models (database table definitions)
- **`app/auth.py`** — JWT auth using PyJWT + bcrypt; `get_current_user` FastAPI dependency
- **`app/clerk_auth.py`** — Clerk JWT validation for the new auth flow; `get_current_clerk_user` dependency
- **`app/repositories/`** — Repository pattern with pluggable backends:
  - `base.py` — Abstract interfaces (`PersonRepository`, `EventRepository`, etc.)
  - `memory.py` — In-memory implementations (default for dev)
  - `postgresql.py` — PostgreSQL implementations (production)
  - `__init__.py` — Factory functions (`get_person_repository`, etc.) that return the right implementation
- **`app/routers/`** — FastAPI route handlers: `person`, `event`, `attendance`, `user`, `groups`, `sms`
- **`app/services/sms_service.py`** — Twilio SMS integration

The repository factory pattern means all routers call `get_person_repository(db)` etc. — the `db` parameter is only used when `DATABASE_TYPE=postgresql`.

### Frontend (`frontend/src/`)

- **Framework**: Astro with React islands (`output: 'server'`, deployed to Vercel)
- **UI**: Material UI v7 with dark theme
- **State**: Nanostores (`stores/auth.ts`) for auth state; localStorage for token persistence
- **Auth**: Clerk (`@clerk/astro`) is the primary auth provider; legacy JWT flow also exists
- **API calls**: `stores/auth.ts` exports `apiRequest()` which handles Clerk token injection and 401 redirects
- **Pages** (`src/pages/`): Astro pages — `index`, `People`, `Events`, `checkin`, `Messaging`, `sign-in`, `sign-up`
- **Components** (`src/components/`): React components rendered as islands — `PersonList`, `EventList`, `CheckIn`, `PersonForm`, `MessagingPage`, `Navigation`, etc.
- **`src/middleware.ts`** — Astro middleware (likely for Clerk auth protection)

### Key Env Variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_TYPE` | `memory` | `memory` or `postgresql` |
| `DATABASE_URL` | — | PostgreSQL connection string |
| `SECRET_KEY` | (insecure default) | JWT signing key |
| `ADMIN_PASSWORD` | (random) | Initial admin account password |
| `CLERK_SECRET_KEY` | — | Clerk backend validation |
| `PUBLIC_API_URL` | `http://localhost:8000` | Frontend API base URL (Astro public env) |
| `TWILIO_*` | — | SMS sending credentials |

### Data Model Relationships

All tables use `BigInteger` PKs. Key relationships:

- **`PersonDB`** — unified table for `youth`, `leader`, and `parent` person types. Youth-specific fields (grade, school, birth_date, allergies, emergency contacts) and leader-specific fields (role) are nullable and only populated for the relevant type.
- **`EventDB` ↔ `PersonDB`** — linked via `EventPersonDB` (junction table); records check-in/check-out times and the person's type at time of attendance.
- **`ParentYouthRelationshipDB`** — self-referential M2M on `PersonDB`; both `parent_id` and `youth_id` are FKs to `persons`. Tracks relationship type (mother/father/guardian) and primary contact flag.
- **`MessageGroupDB` → `PersonDB`** — via `MessageGroupMembershipDB` junction table (unique on `group_id + person_id`).
- **`MessageDB`** — belongs to a `MessageGroupDB` (nullable, for individual messages); tracks per-message delivery status, Twilio SID, and optionally links to a `PersonDB` recipient.
- **`MessageTemplateDB`** — standalone; unique per `(name, created_by)` pair.
- **`UserDB`** — internal app users (legacy JWT auth); separate from Clerk users. Clerk user IDs are stored as plain strings (`sent_by`, `created_by`, `added_by`) with no FK.

### Backend Tests

- Most tests are under `backend/tests/`. The `conftest.py` at `backend/` level auto-starts a Docker PostgreSQL container for database tests.
- Tests that use the `test_db` fixture require Docker; pure unit tests (e.g., `test_backend_admin_security.py`) run without Docker.
- `DATABASE_TYPE=memory` skips DB tests — set `DATABASE_TYPE=postgresql` to run them.

### Docs

- **`docs/api/endpoints.md`** — API endpoint reference
- **`docs/feature-flags.md`** — feature flag naming conventions and types (`release`, `kill-switch`, `experiment`, `migration`, `show`, `allow`)
