# MindMap OS

A visual second-brain / personal knowledge management system. Capture ideas,
notes, projects, and resources as nodes, connect them into a knowledge graph,
and explore, search, and get rule-based suggestions across everything you've
captured.

> Every piece of knowledge is a node. Every relationship is an edge.

## Features

- **Interactive knowledge graph** (React Flow) — pan, zoom, drag, connect and
  delete edges, filter by type, click to focus on a node's neighborhood,
  double-click to open it. **Your arrangement is saved automatically** —
  drag a node and its position persists across refreshes and revisits (see
  "Graph layout persistence" below)
- **Full-text search** across titles, descriptions, content, tags, and
  resources, backed by PostgreSQL `tsvector` and cached in Redis
- **Tags & relationships** — an 11-type relationship vocabulary (`REQUIRES`,
  `INSPIRES`, `CONTRADICTS`, `SUPPORTS`, …) with duplicate- and
  self-reference prevention
- **Dashboard** — node/connection/tag counts, a 30-day growth chart, recent
  and favorite nodes, knowledge density
- **Analytics** — most-connected nodes, tag usage, rule-based connection
  suggestions (shared-tag heuristic; explicitly not "AI" — see below)
- **Activity log** — a permanent, timestamped history of what you've built
- **JWT auth with real revocation** — access + refresh tokens, argon2
  password hashing, per-user data isolation enforced server-side on every
  endpoint, and logout actually blacklists the token in Redis (not just a
  client-side discard)
- **Redis with real jobs** — response caching (with invalidation on writes),
  rate limiting (now actually applied — see below), recently-viewed nodes,
  popular-node tracking, JWT blacklist
- **Light/dark/system theme**, empty states, skeleton loaders, consistent
  API error envelope
- **Production-hardened** — fail-fast config validation, security headers,
  multi-worker production server, static frontend build served via nginx
  (see "Production deployment" below)

## Graph layout persistence

Node positions (`position_x`, `position_y` on `knowledge_nodes`) are `NULL`
until you drag a node for the first time. The frontend:

1. On load, uses each node's saved position if it has one; nodes that have
   never been placed get a computed fallback (concentric-ring) layout
2. Immediately persists that fallback layout via `POST /graph/positions`, so
   even a first-ever visit is stable from the next reload onward
3. On every drag-stop, saves the new position (debounced/batched if you move
   several nodes quickly) via the same endpoint

This means your arrangement survives a refresh, navigating to another page
and back, and logging back in later — it's stored server-side per node, not
in browser state.

## Tech stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x (async), PostgreSQL,
Redis, Alembic, JWT (python-jose), argon2 password hashing, pytest

**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, React Router,
TanStack Query, Zustand, React Flow, Recharts

**Infra:** Docker Compose (postgres, redis, backend, frontend); nginx for
the production frontend build

## Architecture

```
frontend (Vite/React) ──REST──▶ backend (FastAPI)
                                     │
                          ┌──────────┼──────────┐
                          ▼                     ▼
                     PostgreSQL              Redis
                (source of truth)   (cache, rate limits,
                                      recent/popular nodes)
```

Backend layout follows a light service/repository split — routers stay thin
(auth + validation + delegate), services own business logic and cache
invalidation, repositories own query construction:

```
backend/app/
├── main.py                 FastAPI app, middleware, exception handlers
├── core/                   config, JWT/password utils, auth dependency
├── db/                     async SQLAlchemy engine, Redis client + helpers
├── models/                 SQLAlchemy 2.x ORM models
├── schemas/                Pydantic request/response models
├── repositories/           query construction (node_repository)
├── services/                business logic, cache invalidation, activity log
├── api/v1/                 routers, one per resource
├── middleware/              request logging, error handlers
├── seed.py                 demo-account seed script
└── tests/                   pytest suite (auth, nodes, relationships)
```

### Database schema

`users → knowledge_nodes → {node_tags↔tags, resources, relationships,
activities}`. Every foreign key cascades appropriately; `relationships` has
a `CHECK (source_node_id != target_node_id)` constraint and a unique
constraint on `(source, target, type)` to prevent self-loops and duplicate
edges at the database level, not just in application code.

### Redis architecture

| Responsibility     | Keys                              | Notes                          |
|---------------------|------------------------------------|---------------------------------|
| Cache                | `dashboard:user:{id}:*`, `search:{id}:*`, `graph:user:{id}:*` | invalidated on every relevant write |
| Rate limiting         | `ratelimit:{path}:{identifier}`   | fixed-window counter, applied to every route by default (see below) |
| Recently viewed       | `recent:user:{id}`                | Redis list, capped at 20        |
| Popular nodes          | `popular:user:{id}`               | Redis sorted set, incremented on view |
| JWT blacklist          | `blacklist:{jti}`                 | set on logout, TTL = token's remaining lifetime |

### Rate limiting — and a bug worth knowing about

Every route under `/api/v1` goes through a general rate limit (100/min by
default) applied at the router level; `/auth/register`, `/auth/login`, and
`/auth/refresh` additionally get a stricter limit (10/min) since they're the
highest-value target for brute-force/credential-stuffing.

**A real bug was caught and fixed here during development**: the rate-limit
dependency originally took a plain `limit: int = ...` parameter. FastAPI
resolves un-annotated primitive parameters on a dependency as *query
parameters of the route*, so any endpoint with its own `?limit=N` query
param (pagination, effectively everywhere) silently overrode the intended
rate-limit ceiling with whatever the client passed — `/nodes?limit=2` capped
the rate limit at 2 requests instead of 100. Fixed by refactoring to a
closure-based factory (`rate_limiter(ceiling)`) so the ceiling is baked in
and never exposed as a request parameter at all. There's a permanent
regression test for this in `tests/test_nodes.py`.

### Authentication flow

`POST /auth/register` → `POST /auth/login` returns a short-lived access
token (15 min default) and a longer-lived refresh token (7 days default).
The frontend's Axios client automatically retries a 401 once by calling
`POST /auth/refresh`, then redirects to `/login` if that also fails. JWT
payloads carry only `sub` (user id), `type`, `iat`, `exp`, and `jti` —
nothing sensitive.

**Logout is stateful, not just client-side.** `POST /auth/logout` decodes
the access token's `jti` and blacklists it in Redis with a TTL matching its
remaining lifetime, so a copied/leaked token stops working immediately
instead of staying valid for up to 15 more minutes. If the client also sends
its refresh token in the logout request body, that gets blacklisted too.
`get_current_user` and the refresh flow both check the blacklist before
trusting an otherwise-valid, non-expired token.

### Suggestions — deliberately not "AI"

`suggestion_service.py` implements a deterministic, explainable heuristic:
nodes that share a tag but aren't yet connected are surfaced with a stated
reason. The architecture (a single service function returning a flat list of
`{node_a, node_b, reason, factor}`) is intentionally left open for a future
embedding-based engine to slot in behind the same API without changing the
frontend.

## Local setup

### Prerequisites
- Docker & Docker Compose (recommended), **or** Python 3.12+, Node 20+,
  PostgreSQL 16, and Redis 7 installed locally

### Option A — Docker Compose (recommended)

```bash
cp .env.example .env
# Edit .env and set a real JWT_SECRET_KEY:
#   python -c "import secrets; print(secrets.token_urlsafe(64))"

docker compose up --build
```

This starts postgres, redis, the backend (migrations run automatically on
container start via `entrypoint.sh`), and the frontend dev server.

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs (Swagger) and `/redoc`

Seed demo data (from the host, once containers are up):

```bash
docker compose exec backend python -m app.seed
```

Demo login: `demo@mindmapos.app` / `DemoPassword123!` — **development only**,
never use this account or password in production.

### Option B — run natively

```bash
# Backend
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql+asyncpg://mindmap:mindmap@localhost:5432/mindmap
export REDIS_URL=redis://localhost:6379/0
alembic upgrade head
python -m app.seed        # optional, generates demo data
uvicorn app.main:app --reload

# Frontend, in a second terminal
cd frontend
npm install
npm run dev
```

## Environment variables

See [`.env.example`](.env.example) for the full list. Never commit a real
`.env` file. At minimum, generate a real `JWT_SECRET_KEY` before doing
anything beyond local development:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## Production deployment

```bash
cp .env.example .env
# Edit .env:
#   ENV=production
#   JWT_SECRET_KEY=<real generated secret, 32+ chars>
#   CORS_ORIGINS=https://your-real-frontend-domain.com
#   VITE_API_BASE_URL=https://your-real-api-domain.com/api/v1

docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

What changes vs. local dev:

- **Config fails fast at startup** if `JWT_SECRET_KEY` is a placeholder or
  too short, or if `CORS_ORIGINS` still points at localhost or `*`, with
  `ENV=production` — the process refuses to boot rather than silently
  serving traffic insecurely
- **Backend runs multi-worker uvicorn** (`--workers`, default 4, tune via
  `WEB_CONCURRENCY`), no `--reload`, no `Server` response header, and the
  security-headers middleware adds HSTS + a strict CSP
- **Frontend is a static build served by nginx** (`Dockerfile.prod`), not
  the Vite dev server — the dev server has no production hardening and
  isn't meant to be internet-facing. `VITE_API_BASE_URL` is baked into the
  JS bundle at *build* time (Vite convention), so changing it requires a
  rebuild, not just a container restart
- **No source bind-mounts** — containers run exactly what was built into
  the image, not whatever's currently on the host filesystem
- **Postgres/Redis ports aren't published to the host** — only the backend
  container needs to reach them, over the internal Docker network

⚠️ **The `docker-compose.prod.yml` override uses the `!reset` YAML tag**
(to fully clear the dev file's bind-mounts and port publications rather than
append to them), which requires **Docker Compose v2.24+** (Jan 2024). This
specific file could not be verified with a real `docker compose` run in the
environment this was built in (no Docker available there — see
"Verification" below). If `up` fails immediately on that tag, either upgrade
Docker Desktop, or delete the `volumes: !reset []` / `ports: !reset []`
lines as a fallback (you'll keep the dev bind-mounts and published DB ports,
which is a minor hardening gap, not a functional break).

## Testing

```bash
cd backend
export DATABASE_URL=postgresql+asyncpg://mindmap:mindmap@localhost:5432/mindmap_test
export REDIS_URL=redis://localhost:6379/1
pytest -v
```

The suite covers auth (register/login/refresh/token-type validation, logout
JWT revocation), node CRUD/ownership isolation/pagination/filtering,
relationship rules (duplicate prevention, self-reference rejection,
ownership checks), and a regression test for the rate-limit query-param
collision bug described above. All 24 tests were run and pass against a
real PostgreSQL + Redis instance as part of building this project — see
"Verification" below.

## Verification

Everything in this repo was exercised against real infrastructure while
building it, not just written and assumed to work:

- Backend imports cleanly and all 23 paths (29 route operations across
  GET/POST/PATCH/DELETE) register correctly (verified via FastAPI's OpenAPI
  schema)
- The hand-written Alembic migrations were run against a live PostgreSQL 16
  database (including the later migration adding `position_x`/`position_y`)
  and the resulting schema was inspected directly via `psql`
- The full pytest suite (24 tests) was run against real Postgres + Redis —
  across the two rounds of building this, this caught and led to fixing six
  real bugs:
  - a non-JSON-serializable validation error
  - a `MissingGreenlet` error from a missing `db.refresh()` after a
    server-side `onupdate` column changed
  - duplicate enum-type creation in the initial migration
  - `.local` being rejected as an IANA special-use TLD by the email
    validator (demo account domain changed)
  - a missing eager-load of tags in the search query causing a 500
  - **the rate-limit query-parameter collision** described above, caught
    because the real test suite started 429-ing on ordinary pagination
    calls the moment rate limiting was actually turned on
- Graph position persistence was verified end-to-end with direct `curl`
  calls against a live server: saved a set of node positions, re-fetched
  `GET /graph`, and confirmed the exact same coordinates came back —
  confirming it survives what would be a page refresh. Ownership checks on
  `POST /graph/positions` were also verified (a foreign/nonexistent node id
  correctly 404s)
- The production config validator was verified in both directions: a
  placeholder secret, a too-short secret, and a localhost CORS origin were
  each confirmed to raise and refuse to boot under `ENV=production`; a
  properly-configured production env was confirmed to start cleanly; dev
  mode was confirmed to never be blocked regardless of secret strength
- Security headers were verified present on real responses in both dev mode
  (baseline headers only) and production mode (adds HSTS + CSP)
- The full production `entrypoint.sh` (migrations → multi-worker uvicorn
  with `--no-server-header`, `--timeout-keep-alive`) was run end-to-end and
  confirmed to serve real traffic correctly
- The frontend was installed, type-checked (`tsc -b`, zero errors), and
  built for production (`vite build`) successfully; a path-alias bug caught
  by the real build (not just `tsconfig.json`) was fixed. Route-level code
  splitting was added after the initial build flagged an 837KB bundle
  (react-flow and recharts now lazy-load only on the routes that use them)
- `Dockerfile.prod`'s build-arg approach for `VITE_API_BASE_URL` was
  verified directly: built the frontend with a custom API URL set as an
  env var (mirroring what the Docker `ARG`/`ENV` pair does) and confirmed
  the URL was actually compiled into the output JS bundle
- **Not verified:** `docker compose up --build` itself — for either the dev
  or the new production compose files — was not run, because Docker isn't
  available in the environment this was built in. Every command each
  Dockerfile/entrypoint actually runs (`alembic upgrade head`, `uvicorn`
  with the exact production flags, `npm run build`) was verified directly
  and confirmed working; what's unverified is Docker's own build/orchestration
  layer on top of those commands, plus the `!reset` YAML tag's compatibility
  with your specific Compose version (see "Production deployment" above).

## Demo account

```
email:    demo@mindmapos.app
password: DemoPassword123!
```

Development/demo only — do not reuse this password anywhere, and don't rely
on this account existing outside of a freshly seeded local database.

## Future improvements

- Background jobs (Celery/ARQ) for resource metadata (OpenGraph) fetching,
  currently a stub comment in `resources.py`
- WebSocket-based real-time graph updates for the user's own open sessions
- An "Add Relationship" button on the node detail page — connecting nodes
  currently only works via drag-and-drop on the Graph page
- A force-directed graph layout for a node's *fallback* position (currently
  a deterministic concentric-ring layout, legible but not physics-based);
  once a node is dragged its position is saved and this no longer applies
- Frontend test coverage (backend has real test coverage; the frontend was
  only type-checked and build-verified in this pass)
- A `robots.txt`/security.txt and dependency vulnerability scanning
  (`npm audit`, `pip-audit`) as part of a CI pipeline — none of that exists
  yet, this repo has no CI configured at all
