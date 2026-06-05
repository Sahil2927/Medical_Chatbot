# MediAssist frontend plan

## Stack (confirmed)

- React 18 + TypeScript + Vite
- Tailwind CSS
- lucide-react icons
- react-router-dom
- FastAPI backend (existing); mock REST APIs in Phase 2

## Phases

### Phase 1 — UI shell (done)

- MediAssist layout: sidebar, header, welcome, 4 quick-action cards, composer
- Reusable UI: `Button`, `Card`, `IconButton`, `Badge`
- Local-only chat state (`useChat`); no network calls
- No voice/mic (removed from plan)
- Attach button wired in Phase 3

### Phase 2 — REST mock APIs (done)

- `GET /api/mock/status`
- `GET /api/conversations`
- `POST /api/conversations` (optional `content` + `mode`)
- `GET /api/conversations/{id}`
- `GET /api/conversations/{id}/messages`
- `POST /api/conversations/{id}/messages` → user + assistant exchange
- CORS for Vite dev (`localhost:5173`)
- React client wired via `frontend/src/api/`

### Phase 3 — Upload (done)

- [x] `POST /api/conversations/{id}/attachments` (multipart; PDF and TXT only; text-extractable; max 5 MB; no images)
- [x] Lab Results mode: extract text from PDF/TXT and run B6 parser
- [x] Composer attach button enabled in React

### Phase 4 — Production static build (done)

- [x] `cd frontend && npm run build` → `frontend/dist/`
- [x] FastAPI serves SPA when `frontend/dist/index.html` exists (`src/frontend_static.py`)
- [x] Same origin: UI calls `/api` with empty `VITE_API_BASE` (no Vite proxy required)
- [x] Optional `FRONTEND_DIST` / `SERVE_FRONTEND` env overrides

### Phase 5 — Real backends + metadata UI (done)

- [x] All modes backed by live services
- [x] Crisis helpline panel + parsed lab results cards on assistant messages (`MessageMetadata`)
- [x] Metadata persisted on assistant messages and returned in message history

## REST conventions (Phase 2+)

- Nouns for resources, plural collections
- JSON request/response bodies
- `201` on create, `404` for missing conversation, `422` validation errors
- ISO-8601 timestamps in responses
