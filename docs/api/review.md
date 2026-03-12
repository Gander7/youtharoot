# API Architecture Review

**Reviewer:** Senior API Architect
**Date:** 2026-03-12
**Subject:** Youtharoot REST API — Current State Analysis & Proposed Changes

---

## Executive Summary

The API has a solid foundation in FastAPI with a clean repository pattern underneath, but the surface layer has accumulated several structural inconsistencies. The main issues are: no versioning, fragmented resource naming (singular/plural mixing, an orphaned `/api/sms` prefix), two incompatible auth systems coexisting with most endpoints having auth completely disabled, no standard error envelope, and HTTP semantics that are frequently incorrect (wrong status codes, actions disguised as resource updates). The changes proposed here are ordered by impact. None require changes to the repository or business logic layer — they are all routing and response-shaping concerns.

---

## Issue Index

| # | Severity | Category | Issue |
|---|----------|----------|-------|
| 1 | Critical | Auth | Auth disabled on person, event, and attendance endpoints |
| 2 | Critical | Auth | Two incompatible auth systems with no migration path |
| 3 | High | Structure | No API versioning |
| 4 | High | Naming | Inconsistent singular/plural resource names |
| 5 | High | Naming | `/api/sms` prefix breaks namespace consistency |
| 6 | High | HTTP | Wrong status codes on create operations |
| 7 | High | HTTP | `DELETE /person/{id}` is a soft-delete — misleading semantics |
| 8 | High | HTTP | Checkout endpoints use `PUT` for actions |
| 9 | Medium | Structure | No standard error response envelope |
| 10 | Medium | Structure | No pagination on list endpoints |
| 11 | Medium | Naming | `/parents/search` should be a query param on `/parents` |
| 12 | Medium | Design | Emergency contacts modelled as flat fields, not a sub-resource |
| 13 | Medium | Design | `GET /event/{id}/attendance` duplicates data available in the event object |
| 14 | Low | Naming | Trailing slash inconsistency on `/users/` endpoints |
| 15 | Low | Design | `GET /groups/{id}/available-members` is an expensive full-table scan |
| 16 | Low | Design | `birth_date` is required on Youth but optional everywhere else inconsistently |

---

## Issue Detail & Proposed Changes

---

### 1. Auth disabled on person, event, and attendance endpoints
**Severity: Critical**

Every person, event, and attendance route has `current_user` commented out with a `# TODO: Re-enable with Clerk` note. These are the most sensitive endpoints in the system — they expose names, birth dates, emergency contacts, allergies, and attendance history.

**Current:**
```python
# current_user: User = Depends(get_current_user_lazy())  # TODO: Re-enable with Clerk
```

**Proposed:**
Re-enable authentication immediately using the Clerk dependency (`get_current_clerk_user`) that already exists and is working in the groups and SMS routers. There is no reason to wait — the dependency is proven.

```python
current_user: dict = Depends(get_current_clerk_user)
```

---

### 2. Two incompatible authentication systems
**Severity: Critical**

The codebase has two auth systems that cannot interoperate:

| System | Token type | Used by |
|--------|-----------|---------|
| Legacy JWT (`app/auth.py`) | Self-signed HS256 JWT | `/users/login`, intended for person/event/attendance |
| Clerk (`app/clerk_auth.py`) | Clerk-issued session JWT | `/groups`, `/api/sms` |

The frontend (`stores/auth.ts`) already shows the conflict — `apiRequest()` tries Clerk's `getToken()` first, then falls back to `localStorage.getItem('token')` from the old system.

**Proposed:**
Commit to Clerk as the single auth provider and deprecate the legacy system. This means:

1. Remove `/users/login` (or keep it as a compatibility shim that redirects to Clerk sign-in for a single transition period).
2. Remove `app/auth.py` `get_current_user` / `create_access_token` once all endpoints use `get_current_clerk_user`.
3. The `/users` CRUD endpoints themselves may still make sense — but access control should come from Clerk roles/metadata, not a separately maintained `users` table.

If a self-hosted auth fallback is genuinely required (offline, no-internet deployments), document that explicitly and keep both systems isolated rather than letting them bleed together via the `apiRequest()` fallback logic.

---

### 3. No API versioning
**Severity: High**

There is no version prefix on any route. The first breaking change — adding a required field, renaming a resource, changing response shape — will break all clients with no migration path.

**Proposed:**
Add a `/v1` prefix to all routes now, before a production deployment is locked in. In FastAPI this is done at the router or app level:

```python
# Option A — app-level prefix (simplest)
app.include_router(person_router, prefix="/v1")
app.include_router(event_router, prefix="/v1")
# ...

# Option B — APIRouter prefix per router
router = APIRouter(prefix="/v1/people")
```

The frontend's `PUBLIC_API_URL` is already an environment variable, so swapping `http://localhost:8000` → `http://localhost:8000/v1` is a one-line config change.

---

### 4. Inconsistent resource naming (singular vs plural, mixed hierarchy)
**Severity: High**

The current URL space is hard to predict:

| Current | Issue |
|---------|-------|
| `GET /person/youth` | Plural collection under singular resource |
| `GET /person/leaders` | Same problem, different word |
| `GET /person/{id}` | Singular |
| `POST /person` | Singular |
| `GET /parents` | Plural |
| `GET /parent/{id}` | Singular |
| `POST /parent` | Singular |
| `GET /parents/search` | Plural, then action |
| `GET /events` | Plural |
| `GET /event/{id}` | Singular |
| `POST /event` | Singular |

REST convention: **collections are plural, individual items are `/{id}` under the collection**.

**Proposed URL map:**

| Current | Proposed |
|---------|----------|
| `GET /person/youth` | `GET /people?type=youth` |
| `GET /person/leaders` | `GET /people?type=leader` |
| `GET /person/{id}` | `GET /people/{id}` |
| `POST /person` | `POST /people` |
| `PUT /person/{id}` | `PUT /people/{id}` |
| `DELETE /person/{id}` | `DELETE /people/{id}` (or `PATCH` — see issue 7) |
| `GET /parents` | `GET /people?type=parent` or keep as `GET /parents` (see below) |
| `GET /parent/{id}` | `GET /parents/{id}` |
| `POST /parent` | `POST /parents` |
| `GET /parents/search` | `GET /parents?q=...` (see issue 11) |
| `GET /events` | `GET /events` ✓ |
| `GET /event/{id}` | `GET /events/{id}` |
| `POST /event` | `POST /events` |
| `PUT /event/{id}` | `PUT /events/{id}` |
| `DELETE /event/{id}` | `DELETE /events/{id}` |

For the `GET /people` unification: the `person_type` filter (`?type=youth`) is simpler than three separate collection endpoints and makes search across all types trivially addable. The response shape is already discriminated by `person_type`, so the client can handle mixed results.

---

### 5. `/api/sms` prefix breaks the namespace
**Severity: High**

Every other resource lives at the root: `/people`, `/events`, `/groups`. The SMS router sits at `/api/sms`, introducing an extra `/api` segment that doesn't exist anywhere else. This implies the rest of the API is *not* an API, which is confusing and makes gateway routing rules harder to write.

**Proposed:** Remove the `/api` prefix segment. Move to `/sms` (or `/messages` — see issue 12 below for context).

```python
# In sms.py
router = APIRouter(prefix="/sms", tags=["SMS"])
```

---

### 6. Wrong status codes on create operations
**Severity: High**

Every `POST` that creates a resource returns `200 OK`. The correct code for a successful creation is `201 Created`. This matters because:
- HTTP clients and caches treat `200` and `201` differently.
- API consumers use the status code to know whether a resource was newly created or already existed.
- `POST /users/` already gets this right (`status_code=status.HTTP_201_CREATED`) — the inconsistency is within the same codebase.

**Affected endpoints:**

| Endpoint | Current | Proposed |
|----------|---------|----------|
| `POST /person` | `200` | `201` |
| `POST /parent` | `200` | `201` |
| `POST /event` | `200` | `201` |
| `POST /event/{id}/checkin` | `200` | `201` |

**FastAPI fix** — one argument:
```python
@router.post("/events", response_model=Event, status_code=201)
```

---

### 7. `DELETE /person/{id}` is a soft-delete — misleading semantics
**Severity: High**

The endpoint is named `archive_person` internally, sets `archived_on`, and returns `{}` with a `200`. The client has no way to know from the HTTP contract that the person still exists in the database. This matters when:
- A client tries to `GET /people/{id}` after a `DELETE` and still gets a `200` (the record isn't gone).
- A client retries a `DELETE` on the same ID expecting `404`.

**Option A — Keep the soft-delete but use `PATCH` + a status field:**
```
PATCH /people/{id}
{ "status": "archived" }
→ 200 OK, returns updated person with archived_on set
```
This is semantically honest — it's an update, not a deletion.

**Option B — Keep `DELETE` but return `204` and document it as an archive:**
```
DELETE /people/{id}
→ 204 No Content
```
And document clearly: *This archives the person rather than permanently deleting them. The record can be recovered.*

Option A is preferred because it preserves discoverability and allows future status transitions (e.g. `active` → `archived` → `active`).

---

### 8. Checkout endpoints misuse `PUT`
**Severity: High**

`PUT /event/{id}/checkout` and `PUT /event/{id}/checkout-all` use `PUT`, which semantically means "replace this resource with the request body." These are **actions** (transitions of state), not resource replacements. The request body contains only a `person_id` — there's no full resource representation being sent.

The correct verb for a state-transition action that doesn't fit neatly into CRUD is `POST` against an action sub-resource:

**Proposed:**

| Current | Proposed |
|---------|----------|
| `PUT /event/{id}/checkout` | `POST /events/{id}/checkout` |
| `PUT /event/{id}/checkout-all` | `POST /events/{id}/checkout-all` |
| `POST /event/{id}/checkin` | `POST /events/{id}/checkin` ✓ (already correct verb, just needs plural) |

Alternatively, model attendance as a proper sub-resource with state:
```
PATCH /events/{id}/attendance/{person_id}
{ "status": "checked_out" }
```
This is more RESTful but a larger refactor. The `POST /action` approach is the pragmatic middle ground.

---

### 9. No standard error response envelope
**Severity: Medium**

FastAPI's default error shape is `{"detail": "..."}`. Custom errors in the codebase sometimes return plain strings, sometimes structured objects, sometimes just raise the default. There is no consistent envelope.

**Proposed — adopt a standard error shape across all endpoints:**

```json
{
  "error": {
    "code": "PERSON_NOT_FOUND",
    "message": "Person with ID 42 was not found.",
    "field": null
  }
}
```

| Field | Purpose |
|-------|---------|
| `code` | Machine-readable constant — use for programmatic handling in the frontend |
| `message` | Human-readable string for display or logging |
| `field` | Which request field caused the error (for validation errors) |

Implement with a FastAPI exception handler:
```python
@app.exception_handler(AppError)
async def app_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "field": exc.field}}
    )
```

Define a small set of error codes (`PERSON_NOT_FOUND`, `ALREADY_CHECKED_IN`, `OPT_OUT_BLOCKED`, `DUPLICATE_GROUP_NAME`, etc.) and use them consistently. This saves the frontend from parsing error strings.

---

### 10. No pagination on list endpoints
**Severity: Medium**

`GET /people?type=youth`, `GET /events`, `GET /parents`, and `GET /groups` all return unbounded lists. As the database grows this becomes a performance and memory problem.

**Proposed — add standard cursor or offset pagination to all list endpoints:**

```
GET /people?type=youth&limit=50&offset=0
```

**Response envelope for lists:**
```json
{
  "data": [ ... ],
  "total": 243,
  "limit": 50,
  "offset": 0
}
```

The SMS history endpoints already implement `limit`/`offset` — apply the same pattern everywhere. Consider cursor-based pagination for high-volume lists to avoid the `COUNT(*)` overhead.

---

### 11. `GET /parents/search` should be a query param
**Severity: Medium**

Having a dedicated `/search` endpoint is an anti-pattern in REST because it creates a path segment collision risk — if someone ever creates a parent with a name that looks like a route, static routes must come before dynamic ones (which FastAPI handles, but it's fragile). More importantly, it's unnecessary: search is just filtering, and filtering belongs on query params.

**Current:**
```
GET /parents/search?query=Jane
```

**Proposed:**
```
GET /parents?q=Jane
```

Or, when people are unified under `/people`:
```
GET /people?type=parent&q=Jane
```

Remove the `/search` endpoint entirely once the query-param version exists.

---

### 12. Emergency contacts modelled as flat fields
**Severity: Medium**

`Youth` has six emergency contact fields: `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relationship`, and a second set for `_2`. This is already at its limit — adding a third contact requires a schema change. The parent-youth link already handles the real relationship graph; emergency contacts feel like a holdover from before that system existed.

**Proposed — either:**

**Option A:** Normalize emergency contacts into the parent relationship system. A parent marked `is_primary_contact: true` is the emergency contact. The flat fields can be deprecated and eventually removed.

**Option B:** Model emergency contacts as a proper sub-resource:
```
GET  /people/{id}/emergency-contacts
POST /people/{id}/emergency-contacts
PUT  /people/{id}/emergency-contacts/{contact_id}
DELETE /people/{id}/emergency-contacts/{contact_id}
```

Option A is lower effort and aligns with existing data. Option B is cleaner long-term if emergency contacts sometimes exist without a full parent record.

---

### 13. `GET /event/{id}/attendance` largely duplicates the event object
**Severity: Medium**

`GET /event/{id}` already returns `youth: [EventPerson]` and `leaders: [EventPerson]` with `check_in` and `check_out`. The attendance endpoint calls `get_person` for every attendee to enrich with name/grade/school and returns a flatter format.

There are two alternatives:

**Option A — Remove the attendance endpoint, enrich the event response:**
Make `GET /events/{id}` return the enriched attendee objects by default (or via `?include=attendance`). This reduces two round trips to one and keeps the data co-located.

**Option B — Keep the attendance endpoint, remove attendees from the event:**
The event becomes a lightweight header object, and attendance is fetched lazily when needed. This is better for the events list (`GET /events`) which currently returns full attendee arrays for every event — that is wasteful.

Option B is the better architectural fit. The events list endpoint should not return attendee arrays at all (they already have separate `youth_count`/`leaders_count` fields for this reason).

---

### 14. Trailing slash inconsistency on `/users/` endpoints
**Severity: Low**

`GET /users/` and `POST /users/` have a trailing slash. Every other endpoint in the API does not. This causes `307 Temporary Redirect` for clients that call `GET /users` (no slash), which is a silent failure in some HTTP clients.

**Proposed:** Remove trailing slashes from user endpoints, or configure FastAPI globally:
```python
app = FastAPI(redirect_slashes=False)
```

---

### 15. `GET /groups/{id}/available-members` is an unbounded full scan
**Severity: Low**

This endpoint fetches all non-archived youth, all leaders, and all parents — three separate full-table reads — to show who *could* be added to a group. As the person database grows this will be slow.

**Proposed:**
This query pattern belongs with search/filtering, not as a fixed endpoint. Replace with:
```
GET /people?exclude_group={group_id}&limit=50&q=...
```

The client search UI already needs a `q` param for live search anyway. Let the person list endpoint do the work with an `exclude_group` filter pushed down to the database query.

---

### 16. `birth_date` is required on Youth but inconsistently optional elsewhere
**Severity: Low**

`Youth.birth_date` is `datetime.date` (required). `Leader.birth_date` and `Parent.birth_date` are `Optional[datetime.date]`. `EventCreate` documents times as Halifax timezone but there's no validator enforcing the `YYYY-MM-DD` format on `date`. `PersonCreate.birth_date` is optional even when `person_type` is `youth`.

**Proposed:**
- Add a Pydantic validator on `PersonCreate` that makes `birth_date` required when `person_type == "youth"`.
- Add a validator on `EventCreate.date` enforcing `YYYY-MM-DD` format (currently enforced only in `_generate_utc_datetimes` at runtime).
- Document the timezone expectation explicitly in the API (all times are Halifax `America/Halifax`).

---

## Proposed Endpoint Map (Final State)

After applying all changes, the surface area becomes:

```
# Versioned root
/v1/

# People (unified)
GET    /v1/people                          ?type=youth|leader|parent&q=...&limit=&offset=
GET    /v1/people/{id}
POST   /v1/people                          → 201
PUT    /v1/people/{id}
PATCH  /v1/people/{id}                     (partial update / archive)

# Parent↔Youth relationships
GET    /v1/people/{youth_id}/parents
POST   /v1/people/{youth_id}/parents       → 201
PUT    /v1/people/{youth_id}/parents/{parent_id}
DELETE /v1/people/{youth_id}/parents/{parent_id}
GET    /v1/people/{parent_id}/children

# Events
GET    /v1/events                          ?days=&name=&limit=&offset=
GET    /v1/events/{id}
POST   /v1/events                          → 201
PUT    /v1/events/{id}
DELETE /v1/events/{id}
GET    /v1/events/{id}/can-delete

# Attendance (actions on events)
GET    /v1/events/{id}/attendance
POST   /v1/events/{id}/checkin             → 201
POST   /v1/events/{id}/checkout
POST   /v1/events/{id}/checkout-all

# Groups (Clerk auth)
GET    /v1/groups                          ?limit=&offset=
GET    /v1/groups/{id}
POST   /v1/groups                          → 201
PUT    /v1/groups/{id}
DELETE /v1/groups/{id}
GET    /v1/groups/{id}/members
POST   /v1/groups/{id}/members             → 201
POST   /v1/groups/{id}/members/bulk        → 201
DELETE /v1/groups/{id}/members/{person_id}

# SMS / Messages (Clerk auth)
POST   /v1/sms/send
POST   /v1/sms/send-group
GET    /v1/sms/history                     ?group_id=&limit=&offset=
GET    /v1/sms/history/top-level           ?days=&limit=&offset=
GET    /v1/sms/history/groups/{id}/details ?message_content=&send_time=
GET    /v1/sms/messages/{id}               (replaces /status/{id})
GET    /v1/sms/analytics                   ?start_date=&end_date=
POST   /v1/sms/webhook                     (Twilio, no auth)

# Auth
POST   /v1/auth/login                      (legacy, deprecate)

# System
GET    /health
```

---

## Priority Order for Implementation

### Phase 1 — Security (do now, before any production traffic)
1. Re-enable Clerk auth on all person, event, and attendance endpoints.
2. Stop falling back to localStorage legacy token in `apiRequest()`.

### Phase 2 — Correctness (low risk, high signal)
3. Fix status codes on all create endpoints (`200` → `201`).
4. Fix `DELETE /person/{id}` to return `204` and document archive semantics.
5. Fix checkout endpoints from `PUT` to `POST`.
6. Remove trailing slash from `/users/` routes.
7. Move `/api/sms` prefix to `/sms`.

### Phase 3 — Naming (coordinate with frontend)
8. Pluralise all collection routes (`/person` → `/people`, `/event` → `/events`).
9. Merge `/person/youth` and `/person/leaders` into `GET /people?type=...`.
10. Merge `/parents/search` into `GET /parents?q=...`.

### Phase 4 — Structural (most effort, most value long-term)
11. Add `/v1` versioning prefix.
12. Add pagination envelope to all list endpoints.
13. Adopt standard error response envelope.
14. Replace `GET /groups/{id}/available-members` with `GET /people?exclude_group={id}`.

### Phase 5 — Model improvements (requires migration)
15. Evaluate consolidating emergency contact flat fields into the parent relationship system.
16. Remove attendee arrays from the events list response; fetch attendance separately.
