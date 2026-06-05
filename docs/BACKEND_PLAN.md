# MediAssist backend implementation plan

Skips frontend Phase 4 (static serve). Phase 3 upload implemented. Focus: real backend behind existing REST API.

---

## Current structure (as of Phase 2)

```text
app.py                      # FastAPI entry → create_app()
src/app_factory.py          # App wiring, CORS, routes, lifespan
src/config.py               # Env: PINECONE_API_KEY, GROQ_API_KEY, index name
src/schemas.py              # Legacy: ChatRequest, ChatResponse, HealthResponse
src/rag.py                  # Pinecone + HuggingFace embeddings + Groq RAG chain
src/prompt.py               # System prompt for RAG
src/helper.py               # PDF load, chunk, embeddings
src/api/appointments_router.py  # GET /api/providers, POST /api/appointments
src/db/appointment_store.py     # Provider lookup + slot holds
src/db/seed.py                  # Seed providers from data/providers_seed.json
src/appointment_schemas.py      # Provider/Appointment DTOs
src/mock/
  router.py                 # REST /api/conversations, /api/mock/status
  store.py                  # In-memory mock store (singleton mock_store)
  schemas.py                # REST DTOs
store_index.py              # One-off Pinecone indexing from data/*.pdf
```

### Knowledge base (runtime)

| Asset | Location |
|-------|----------|
| Source PDF | `data/Medical_book.pdf` (Gale Encyclopedia of Medicine) |
| Vectors | Pinecone index `medical-chatbot` (384-dim, cosine) |
| LLM | Groq `llama-3.1-8b-instant` |

---

## API inventory

### MediAssist REST (mock — target for real implementation)

| Method | Path | Status | Purpose |
|--------|------|--------|---------|
| GET | `/api/mock/status` | Mock | API capability discovery |
| GET | `/api/conversations` | Mock | List threads |
| POST | `/api/conversations` | Mock | Create thread (`title?`, `mode?`, `content?`) |
| GET | `/api/conversations/{id}` | Mock | Get thread metadata |
| GET | `/api/conversations/{id}/messages` | Mock | Message history |
| POST | `/api/conversations/{id}/messages` | Live | Send message → assistant reply |
| GET | `/api/providers` | Live | List providers (`?specialty=`) |
| POST | `/api/appointments` | Live | Hold appointment slot (mock) |

### Legacy / infra

| Method | Path | Status | Purpose |
|--------|------|--------|---------|
| GET | `/health` | Live | Liveness + `rag_ready` |
| POST | `/api/chat` | Live RAG | Single-shot chat (no conversation id) |
| POST | `/get` | Live RAG | Form-compatible alias |
| GET | `/` | Legacy UI | Jinja `chat.html` |

---

## Backend phases

### Phase B1 — Foundation (current sprint)

- [x] `create_app(load_rag_on_startup=False)` for tests
- [x] Unit tests: mock store, mock API, health, legacy chat (mocked RAG)
- [x] CI command: `pytest` (`.github/workflows/ci.yml` on push/PR)

### Phase B2 — Service layer + mode routing (done)

- [x] `src/services/chat_service.py` — `ChatService.send_message()`, `generate_reply()`
- [x] `symptoms` → `invoke_rag()` (Pinecone + Groq)
- [x] `appointment` → `appointment_service.py` (provider stub)
- [x] `mental_health` → `mental_health_service.py` (crisis keyword detection)
- [x] `lab_results` → `lab_results_service.py` (text-only value parsing)
- [x] `mock_store` — persistence only; router delegates to `chat_service`
- [x] REST response schemas unchanged for React

### Phase B3 — Persistence (done)

- [x] PostgreSQL via SQLAlchemy (`postgresql+psycopg2://...`)
- [x] Tables: `conversations`, `messages`
- [x] `PostgresConversationStore` in `src/persistence/conversation_store.py`
- [x] `init_db()` on app startup (creates tables if missing)
- [x] Tests use `sqlite:///:memory:` (same store code path)
- [x] `USE_MEMORY_STORE=true` falls back to in-memory mock (dev only)

### Phase B4 — Appointment backend (done)

- [x] `providers` table / seed JSON (`data/providers_seed.json`)
- [x] `GET /api/providers?specialty=`
- [x] `POST /api/appointments` (hold slot — mock confirm)
- [x] `POST .../messages` for `mode=appointment` — lists providers or holds slot on book intent

### Phase B5 — Mental health backend (done)

- [x] Separate system prompt in `src/prompts/mental_health.py`
- [x] Crisis keyword detector → `metadata` on `MessageExchangeResponse` with helplines (`data/crisis_helplines.json`)
- [x] Groq chat for non-crisis messages (`src/mental_health_llm.py`)
- [x] Optional second Pinecone index via `PINECONE_MENTAL_HEALTH_INDEX_NAME` (`src/mental_health_rag.py`)

### Phase B6 — Lab results (text-only) (done)

- [x] Parse user message for numeric results (`src/services/lab_parser.py`)
- [x] Reference table for common tests (`data/lab_reference.json`, `src/services/lab_reference.py`)
- [x] `metadata.lab_results` on message exchange when values parsed
- [x] PDF/TXT upload in lab mode (`src/services/attachment_service.py`)
- [x] Optional lab RAG index via `PINECONE_LAB_RESULTS_INDEX_NAME` (`src/lab_results_rag.py`) — hybrid parser + book context

### Phase B7 — Production hardening (done)

- [x] Lazy RAG init by default (`LAZY_RAG_INIT=true`); shared embedding singleton; `EAGER_RAG_ON_STARTUP=true` for dev
- [x] Rate limiting on `POST .../messages` and `POST .../attachments` (`RATE_LIMIT_PER_MINUTE`, `0` disables)
- [x] Structured logging + `X-Request-ID` (`src/logging_config.py`, `RequestContextMiddleware`)
- [x] Gate `/api/mock/status` when `ENABLE_MOCK_STATUS=false` or `ENVIRONMENT=production`
- [x] Env feature flags: `ENABLED_MODES=symptoms,appointment,...`

---

## Target architecture (post B2–B3)

```text
Router (HTTP) → Service layer → Adapters
                              ├── RagAdapter (symptoms)
                              ├── AppointmentAdapter
                              ├── MentalHealthAdapter
                              ├── LabResultsAdapter
                              └── ConversationRepository (SQL)
```

---

## Testing strategy

| Layer | Tests |
|-------|--------|
| `MockConversationStore` | Pure unit (no HTTP) |
| Mock REST API | `TestClient` + fresh store per test |
| `create_app(load_rag_on_startup=False)` | Health, validation, 404 |
| RAG `/api/chat` | Mock `invoke_rag` |
| Services (B2+) | pytest with mocked adapters |

Run: `pytest` from repo root.

---

## Environment variables

| Variable | Required | Used by |
|----------|----------|---------|
| `PINECONE_API_KEY` | Yes (RAG) | Pinecone, indexing |
| `GROQ_API_KEY` | Yes (RAG) | Groq LLM |
| `CORS_ORIGINS` | No | FastAPI CORS |
| `DATABASE_URL` | Yes (B3+) | PostgreSQL conversations |
| `PINECONE_MENTAL_HEALTH_INDEX_NAME` | No | Optional mental-health RAG index (B5) |
| `PINECONE_LAB_RESULTS_INDEX_NAME` | No | Optional lab-results RAG index (B6) |
| `MENTAL_HEALTH_TEMPERATURE` | No | Groq temperature for mental health (default `0.4`) |
| `LAB_RESULTS_TEMPERATURE` | No | Groq temperature for lab RAG (default `0.3`) |
| `LAZY_RAG_INIT` | No | Defer RAG until first use (default `true`) |
| `EAGER_RAG_ON_STARTUP` | No | Force startup RAG load (`true` overrides lazy) |
| `RATE_LIMIT_PER_MINUTE` | No | Per-IP POST limit on messages/attachments (`0` = off) |
| `ENVIRONMENT` | No | `development` or `production` |
| `ENABLE_MOCK_STATUS` | No | Expose `/api/mock/status` (default off in production) |
| `ENABLED_MODES` | No | Comma-separated enabled quick-action modes |
| `LOG_LEVEL` | No | Root log level (default `INFO`) |

---

## Frontend contract (unchanged through B2)

React expects JSON shapes in `frontend/src/api/types.ts`. Backend phases must preserve field names: `id`, `title`, `mode`, `created_at`, `updated_at`, `role`, `content`, `conversation_id`.
