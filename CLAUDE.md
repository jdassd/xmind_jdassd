# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A collaborative mind-mapping application supporting 20,000+ nodes with real-time 2-person co-editing. Python/FastAPI backend with MySQL persistence, Vue 3 frontend rendering on Canvas 2D for performance. Includes JWT-based user authentication, team management with role-based permissions, and an invitation system.

## Commands

### Backend
```bash
pip install -r requirements.txt    # Install Python deps
python run.py                      # Start server on port 8080
```

### Frontend
```bash
cd frontend
npm install                        # Install Node deps
npm run dev                        # Dev server with HMR (proxies /api and /ws to localhost:8080)
npm run build                      # Production build (output: frontend/dist/, served by FastAPI)
vue-tsc --noEmit                   # Type-check only (strict mode IS enabled in tsconfig)
```

### Docker
```bash
# With docker-compose (recommended, includes MySQL):
docker-compose up

# Rebuild after code changes (MySQL data persists):
docker-compose up --build
```

### Configuration

`config.yaml` at project root. Environment variables override file values:

| Config | YAML key | Env var | Default |
|--------|----------|---------|---------|
| Port | `port` | `MINDMAP_PORT` | `8080` |
| MySQL host | `db_host` | `MYSQL_HOST` | `127.0.0.1` |
| MySQL port | `db_port` | `MYSQL_PORT` | `3306` |
| MySQL user | `db_user` | `MYSQL_USER` | `mindmap` |
| MySQL password | `db_password` | `MYSQL_PASSWORD` | `mindmap` |
| MySQL database | `db_name` | `MYSQL_DATABASE` | `mindmap` |
| JWT secret | `jwt_secret` | `MINDMAP_JWT_SECRET` | `CHANGE-ME-IN-PRODUCTION` |

Access token lifetime (30 min) and refresh token lifetime (30 days) are hardcoded in `backend/config.py` as `AppConfig` defaults.

## Architecture

### Backend layering

```
routers/          (FastAPI route handlers, request validation via Pydantic)
  auth.py         - /api/auth/*  (register, login, refresh, logout, me)
  maps.py         - /api/maps/*  (CRUD, sync, claim)
  nodes.py        - /api/maps/{id}/nodes/*  (create, update, delete)
  teams.py        - /api/teams/*, /api/invitations/*
  -> services/    (business logic, SQL queries, version bumping)
       auth_service.py
       map_service.py
       node_service.py
       team_service.py
       permission_service.py
  -> db.py        (aiomysql connection pool, MySQL schema init)
  -> auth.py      (JWT creation/validation, password hashing, FastAPI dependencies)
ws/
  handler.py      - WebSocket endpoint /ws/{map_id} (token auth via query param)
  manager.py      - Singleton ConnectionManager with per-map rooms
```

`app.py` is a factory (`create_app()`) used by uvicorn. On startup it creates the MySQL connection pool and initializes the DB schema. On shutdown it closes the pool. After mounting API routes, it conditionally serves `frontend/dist/` as static files.

`get_db()` acquires a connection from the `aiomysql` connection pool (minsize=2, maxsize=10). Connections are returned via `release_db(conn)` in `finally` blocks. All services use `aiomysql.DictCursor` for dict-style row access.

### Authentication flow

1. **Register** (`POST /api/auth/register`): Creates user, auto-logs-in, returns access + refresh tokens.
2. **Login** (`POST /api/auth/login`): Validates credentials, returns access + refresh tokens.
3. **Access token** (JWT, HS256): Contains `sub` (user_id), `username`, `type: "access"`. Expires in 30 minutes.
4. **Refresh token** (JWT, HS256): Contains `sub` (user_id), `type: "refresh"`. Expires in 30 days. Stored as SHA-256 hash in `refresh_tokens` table.
5. **Token rotation** (`POST /api/auth/refresh`): Validates refresh token, **revokes the old one**, issues new access + refresh pair. This means each refresh token is single-use.
6. **Frontend auto-refresh** (`services/api.ts`): The `api()` wrapper intercepts 401 responses, calls `/api/auth/refresh`, retries the original request. Uses a deduplication lock so concurrent 401s only trigger one refresh.
7. **WebSocket auth**: Token passed as query parameter `?token=...` on the WebSocket URL. Validated server-side in `ws/handler.py`.

Tokens are stored in `localStorage` under keys `mindmap_access_token` and `mindmap_refresh_token`.

### Permission model

Role hierarchy: **owner > admin > editor > viewer** (numeric levels 4 > 3 > 2 > 1 in `permission_service.py`).

**Map access rules** (`check_map_access`):
- **Legacy maps** (`owner_id = NULL`): Accessible to all authenticated users. Can be claimed via `POST /api/maps/{id}/claim` (first come, first served).
- **Personal maps** (`owner_id` set, `team_id = NULL`): Only the owner has access.
- **Team maps** (`team_id` set): Access determined by user's team role. Viewing requires `viewer+`, editing requires `editor+`, deleting requires `owner`.

**Team operations**:
- Creating a team makes you the `owner` and auto-adds you to `team_members`.
- Inviting members requires `admin+` role. Invitations are sent by email, tracked in `team_invitations` table.
- The team owner cannot be removed.

### Two sync strategies coexist

The frontend has **two independent sync mechanisms** -- this is a critical architectural detail:

1. **REST polling** (`useSync.ts`): Polls `GET /api/maps/{id}/sync?since={version}` every 1 second. Mutations go through REST endpoints under `/api/maps/{id}/nodes/`. This is the **currently active** path -- `MapEditorPage.vue` provides `syncActions` from `useSync`.

2. **WebSocket** (`useWebSocket.ts`): Connects to `ws://.../ws/{map_id}?token=...`. Sends node operations as JSON messages (`node:create`, `node:update`, `node:delete`, `node:move`). Server broadcasts to other clients. Includes auto-reconnect with exponential backoff (1s to 10s). This composable is fully implemented but is **not wired into the editor page** -- it would replace the REST polling path.

Both use the same Pinia store mutations (`applyNodeCreate`, `applyNodeUpdate`, `applyNodeDelete`), so switching between them is straightforward.

### Data flow

```
User interaction (Canvas click/keyboard)
  -> Optimistic local update (store.applyNode*)
  -> Sync action (REST POST/PUT/DELETE or WebSocket send)
  -> Server persists to MySQL, bumps map version, logs to change_log table
  -> Other clients pick up changes (via polling sync endpoint or WS broadcast)
```

### Versioning and conflict resolution

- Each mutation increments the map's `version` integer in the `maps` table.
- Every node change is recorded in the `change_log` table (map_id, version, action, node_id).
- The `/api/maps/{id}/sync?since=N` endpoint returns changed/deleted node IDs since version N by reading `change_log`.
- Strategy is **Last-Write-Wins** -- no OT or CRDT.

### Canvas rendering pipeline

All node rendering happens in `MindMapCanvas.vue` via the Canvas 2D API (not DOM). The pipeline:

1. Flat node list (from server) -> `buildTree()` (tree.ts) -> hierarchical tree
2. Tree -> `computeLayout()` (layout.ts) -> `LayoutResult` with x/y/width/height per node
3. `draw()` in MindMapCanvas applies viewport transform, culls nodes outside visible area, draws connections (bezier curves) then nodes (rounded rects + text)

Layout constants in `layout.ts`: `NODE_H_GAP=40`, `NODE_V_GAP=10`, `NODE_MIN_WIDTH=80`, `NODE_HEIGHT=36`.

### Frontend routing and auth guards

Vue Router with `createWebHistory`. Auth guard in `router.beforeEach`:
- Routes with `meta: { auth: true }` redirect unauthenticated users to `/login` (preserving redirect query).
- Routes with `meta: { guest: true }` redirect authenticated users to `/`.
- Auth store calls `init()` (fetches `/api/auth/me`) before the app mounts, so the guard always has current auth state.

Routes: `/login`, `/register` (guest-only), `/` (home/map list), `/map/:id` (editor), `/teams`, `/teams/:id` (team detail).

The `AppHeader` component is shown on all authenticated pages except the map editor (which has its own `Toolbar`).

### Frontend state management

Three Pinia stores:
- **`mindmap`**: Flat `Map<string, MindNode>` plus computed tree root and layout. Every mutation calls `rebuildTree()` which rebuilds the full tree and recomputes layout. `MindMapCanvas` watches `store.layout` to trigger redraws.
- **`auth`**: User object, loading state, login/logout/register actions.
- **`teams`**: Team list and invitation list with CRUD actions.

Sync actions are injected via Vue's `provide`/`inject` (`syncActions` key) in `MapEditorPage.vue`, making the sync mechanism swappable.

### Database schema (MySQL 8.0)

Ten tables:
- `maps` (id, name, version, owner_id, team_id, created_at, updated_at)
- `nodes` (id, map_id, parent_id, content, position, style, collapsed, version, created_at, updated_at)
- `change_log` (id autoincrement, map_id, version, action, node_id, created_at)
- `users` (id, username, email, password_hash, display_name, created_at, updated_at)
- `refresh_tokens` (id, user_id, token_hash, expires_at, created_at)
- `teams` (id, name, owner_id, created_at, updated_at)
- `team_members` (team_id, user_id, role CHECK in owner/admin/editor/viewer, created_at) -- composite PK
- `team_invitations` (id, team_id, inviter_id, invitee_email, role, status CHECK in pending/accepted/declined, created_at)
- `node_history` (id auto_increment, node_id, map_id, user_id, username, action, old_content, new_content, old_parent_id, new_parent_id, old_position, new_position, snapshot, map_version, created_at)
- `node_locks` (node_id PK, map_id, user_id, username, locked_at)

Schema creation is in `db.py init_db()` using `CREATE TABLE IF NOT EXISTS`. UUID columns use `VARCHAR(36)`. The MySQL database runs as a separate Docker service with a named volume for persistence.

## Key conventions

- Node IDs are UUIDs generated client-side (`crypto.randomUUID()`) and sent to the server, enabling optimistic UI updates before server confirmation.
- The root node of each map has `parent_id = NULL` and cannot be deleted.
- Node `style` is stored as a JSON string (default `"{}"`) but is not currently parsed or used by the renderer.
- The `collapsed` boolean hides a node's entire subtree from both layout calculation and rendering.
- All API endpoints except `/api/auth/register` and `/api/auth/login` require a Bearer token. The `get_current_user` dependency enforces this.
- Password hashing uses bcrypt via passlib. Minimum: 2 chars username, 6 chars password.
- `konva` and `vue-konva` are listed in package.json dependencies but are NOT used -- all rendering is Canvas 2D in `MindMapCanvas.vue`.
- TypeScript strict mode IS enabled in `tsconfig.json`.
- No tests exist in the repository currently.
- No linter or formatter configuration is present.
- Python 3.11+, Node 20+.
