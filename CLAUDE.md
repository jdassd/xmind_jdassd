# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A collaborative mind-mapping application supporting 20,000+ nodes with real-time 2-person co-editing. Python/FastAPI backend with SQLite persistence, Vue 3 frontend rendering on Canvas 2D for performance.

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
vue-tsc --noEmit                   # Type-check only
```

### Docker
```bash
docker build -t mindmap .
docker run -p 8080:8080 -v ./data:/app/data mindmap
```

### Configuration
`config.yaml` at project root. Environment variables (`MINDMAP_PORT`, `MINDMAP_DATABASE`) override file values.

## Architecture

### Two sync strategies coexist

The frontend has **two independent sync mechanisms** -- this is a critical architectural detail:

1. **REST polling** (`useSync.ts`): Polls `GET /api/maps/{id}/sync?since={version}` every 1 second. Mutations (create/update/delete) go through REST endpoints under `/api/maps/{id}/nodes/`. This is the **currently active** path -- `App.vue` provides `syncActions` from `useSync`, not from `useWebSocket`.

2. **WebSocket** (`useWebSocket.ts`): Connects to `ws://.../ws/{map_id}`. Sends node operations as JSON messages (`node:create`, `node:update`, `node:delete`, `node:move`). Server broadcasts to other clients. Includes auto-reconnect with exponential backoff. This composable exists and is fully implemented but is **not wired into `App.vue`** -- it would replace the REST polling path.

Both use the same Pinia store mutations (`applyNodeCreate`, `applyNodeUpdate`, `applyNodeDelete`), so switching between them is straightforward.

### Data flow

```
User interaction (Canvas click/keyboard)
  -> Optimistic local update (store.applyNode*)
  -> Sync action (REST POST/PUT/DELETE or WebSocket send)
  -> Server persists to SQLite, bumps map version, logs to change_log table
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

`NodeRenderer.vue` is a placeholder -- rendering is entirely in the canvas `draw()` function.

Layout constants in `layout.ts`: `NODE_H_GAP=40`, `NODE_V_GAP=10`, `NODE_MIN_WIDTH=80`, `NODE_HEIGHT=36`.

### Backend layering

```
routers/     (FastAPI route handlers, request validation via Pydantic)
  -> services/   (business logic, SQL queries, version bumping)
       -> db.py  (aiosqlite connection factory, WAL mode, schema init)
```

`app.py` is a factory (`create_app()`) used by uvicorn. On startup it initializes the DB schema (with migration fallbacks for adding `version` columns). After mounting API routes, it conditionally serves `frontend/dist/` as static files.

The WebSocket handler (`ws/handler.py`) is mounted as a router and uses a singleton `ConnectionManager` that manages per-map "rooms" with an asyncio lock.

### Database schema (SQLite, WAL mode)

Three tables: `maps` (id, name, version), `nodes` (id, map_id, parent_id, content, position, style, collapsed, version), `change_log` (map_id, version, action, node_id). Foreign keys with CASCADE delete. Indexes on `nodes(map_id)`, `nodes(parent_id)`, `change_log(map_id, version)`.

Each `get_db()` call opens a **new connection** (no connection pool) -- be aware of this if adding concurrent write-heavy features.

### Frontend state management

Single Pinia store (`stores/mindmap.ts`) holds a flat `Map<string, MindNode>` plus a computed tree root and layout. Every mutation calls `rebuildTree()` which rebuilds the full tree and recomputes layout. The `MindMapCanvas` watches `store.layout` to trigger redraws.

Sync actions are injected via Vue's `provide`/`inject` (`syncActions` key) rather than imported directly, making the sync mechanism swappable.

## Key conventions

- Node IDs are UUIDs generated client-side (`crypto.randomUUID()`) and sent to the server, enabling optimistic UI updates before server confirmation.
- The root node of each map has `parent_id = NULL` and cannot be deleted.
- Node `style` is stored as a JSON string (default `"{}"`) but is not currently parsed or used by the renderer.
- The `collapsed` boolean hides a node's entire subtree from both layout calculation and rendering.
- No tests exist in the repository currently.
- No linter or formatter configuration is present.
- Python 3.11+, Node 20+, TypeScript strict mode not enforced (no strict flag in tsconfig).
