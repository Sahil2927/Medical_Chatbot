# MediAssist / Medical Chatbot — Project Report (Complete Context)

**Purpose of this document:** Give a full picture of the project so another AI (e.g. Gemini) can understand architecture, features, data flow, and current status without reading the whole repository.

**Repository path (local):** `E:\Medical Chatbot\Medical_Chatbot`  
**GitHub (referenced in README):** `https://github.com/Sahil2927/Medical_Chatbot.git`  
**Product name in UI:** MediAssist  
**Disclaimer:** Educational medical information only — not diagnosis, not a substitute for licensed clinical care.

---

## 1. Executive summary

MediAssist is a **full-stack medical assistant web application** that started as a simple Flask RAG chatbot and was evolved into:

- **Backend:** FastAPI (Python), PostgreSQL persistence, multiple chat “modes” (symptoms, appointments, mental health, lab results)
- **Frontend:** React 18 + TypeScript + Vite + Tailwind (MediAssist UI)
- **AI / retrieval:** Pinecone vector DB + HuggingFace embeddings + Groq LLM (`llama-3.1-8b-instant`) for **symptoms** mode only
- **Lab results:** Rule-based parsing + JSON reference ranges (no LLM) — supports typed text and **PDF/TXT upload**
- **Deployment target:** Render (single web service: API + built React static files on one port)

**Current local production-style run:** `npm run build` in `frontend/`, then `uvicorn app:app --host 0.0.0.0 --port 8080` → open http://localhost:8080

---

## 2. Problem statement and goals

| Goal | How addressed |
|------|----------------|
| Answer symptom questions from a medical encyclopedia | RAG over `data/Medical_book.pdf` → Pinecone index `medical-chatbot` |
| Structured UX (not one generic chat) | Four quick-action modes with dedicated backend logic |
| Persist conversations | PostgreSQL (`conversations`, `messages` tables) |
| Lab report help without image OCR | PDF/TXT upload → `pypdf` text extraction → regex parser + `lab_reference.json` |
| Single deployable app | Frontend Phase 4: FastAPI serves `frontend/dist/` SPA |
| Safety for mental health | Crisis keyword detection + static helpline metadata (988, etc.) |

---

## 3. Technology stack

### Backend (Python)

| Component | Technology |
|-----------|------------|
| Web framework | FastAPI + Uvicorn |
| ORM / DB | SQLAlchemy 2.x + PostgreSQL (`psycopg2-binary`); SQLite in tests |
| RAG | LangChain + `langchain-pinecone` + `langchain-groq` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| Vector DB | Pinecone index `medical-chatbot`, cosine similarity |
| LLM | Groq API, model `llama-3.1-8b-instant` |
| PDF text extraction | `pypdf` |
| Config | `python-dotenv`, `.env` at repo root |
| Tests | `pytest` (61+ tests passing as of last sprint) |

### Frontend (TypeScript)

| Component | Technology |
|-----------|------------|
| Framework | React 18 |
| Build | Vite 5 |
| Styling | Tailwind CSS |
| Routing | react-router-dom |
| Icons | lucide-react |
| API client | `fetch` in `frontend/src/api/` |

### Data assets

| Asset | Location |
|-------|----------|
| Source medical PDF | `data/Medical_book.pdf` (Gale Encyclopedia of Medicine) |
| Lab reference ranges | `data/lab_reference.json` |
| Crisis helplines | `data/crisis_helplines.json` |
| Provider seed (appointments) | `data/providers_seed.json` |
| User uploads (runtime) | `data/uploads/{conversation_id}/` (gitignored) |

---

## 4. High-level architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (MediAssist React SPA)                                  │
│  /  → index.html    /api/*  → JSON REST                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  FastAPI — src/app_factory.py → create_app()                     │
│  ├── /api/conversations*     (mock_router → ChatService)           │
│  ├── /api/providers, /api/appointments                             │
│  ├── /api/conversations/{id}/attachments (multipart upload)      │
│  ├── /health, /api/chat (legacy RAG), /get (form)                  │
│  └── / + SPA fallback (src/frontend_static.py if dist exists)    │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
  PostgreSQL           Pinecone + Groq      Rule engines
  (conversations,      (symptoms RAG        (lab_parser,
   messages,            only)                appointment,
   providers,                                 mental_health,
   appointments)                              crisis_detector)
```

### Request flow (chat message)

1. `POST /api/conversations/{id}/messages` with `{ "content": "...", "mode": "..." }`
2. `src/mock/router.py` → `build_chat_service()` → `ChatService.send_message()`
3. `ChatService.generate_reply()` branches on `mode`
4. `PostgresConversationStore.add_message_exchange()` saves user + assistant rows
5. Returns `MessageExchangeResponse` (+ optional `metadata` for crisis or lab results)

### Request flow (lab PDF upload)

1. `POST /api/conversations/{id}/attachments` (multipart `file`)
2. `src/services/attachment_service.py` validates `.pdf` / `.txt` only, max 5 MB
3. `_extract_text()` — UTF-8 for txt, `pypdf` for PDF (up to 20 pages)
4. If `conversation.mode == "lab_results"`: `generate_lab_results_reply(extracted_text)`
5. Saves user message with preview + assistant interpretation; returns `metadata.lab_results[]`

---

## 5. Chat modes (four quick actions)

| Mode ID | UI label | Backend behavior | Uses LLM? |
|---------|----------|------------------|-----------|
| `symptoms` | Symptom checking | `invoke_rag()` — Pinecone retrieval + Groq with medical system prompt | Yes (Groq + RAG) |
| `appointment` | Book Appointment | Lists providers from DB seed; booking keywords hold slot via `POST /api/appointments` | No |
| `mental_health` | Mental Health Check-in | Crisis → static helplines + metadata; else Groq with dedicated prompt (`mental_health_llm.py`); optional Pinecone index via `PINECONE_MENTAL_HEALTH_INDEX_NAME` | Yes for non-crisis |
| `lab_results` | Lab Results | Regex parse + `lab_reference.json` → LOW/NORMAL/HIGH + educational notes | No |

Default / no mode: generic educational stub message from `ChatService`.

---

## 6. REST API inventory

### Conversations (primary UI contract)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/mock/status` | API version string, `supported_modes` (phase-b6-…) |
| GET | `/api/conversations` | List threads |
| POST | `/api/conversations` | Create thread; optional `title`, `mode`, `content` |
| GET | `/api/conversations/{id}` | Thread metadata |
| GET | `/api/conversations/{id}/messages` | Message history |
| POST | `/api/conversations/{id}/messages` | Send message → assistant reply |

### Appointments (B4)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/providers?specialty=` | List providers (availability reflects held slots) |
| POST | `/api/appointments` | Hold slot (`provider_id`, optional `conversation_id`, `notes`) |

### Attachments (Frontend Phase 3)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/conversations/{id}/attachments` | Multipart file; PDF/TXT only |

### Legacy / infra

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | `{ "status": "ok", "rag_ready": bool }` |
| POST | `/api/chat` | Single-shot RAG `{ "msg": "..." }` → `{ "answer": "..." }` |
| POST | `/get` | Form POST alias for legacy HTML chat |
| GET | `/docs` | OpenAPI Swagger UI |

### Response metadata (extensions)

`MessageExchangeResponse` may include optional `metadata`:

- **Mental health crisis:** `crisis_detected: true`, `helplines[]` (from `data/crisis_helplines.json`)
- **Lab results:** `lab_results[]` with `test_id`, `name`, `value`, `unit`, `status`, `reference_range`, `note`

Frontend types exist in `frontend/src/api/types.ts` but UI may not render all metadata yet.

---

## 7. Database schema (PostgreSQL)

| Table | Purpose |
|-------|---------|
| `conversations` | `id`, `title`, `mode`, `created_at`, `updated_at` |
| `messages` | `id`, `conversation_id`, `role` (`user`/`assistant`), `content`, `created_at` |
| `providers` | Seeded from `data/providers_seed.json` |
| `appointments` | Mock holds (`status`: `held`), links to `provider_id`, optional `conversation_id` |

**Connection:** `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/mediassist`  
**Important:** If password contains `@`, URL-encode as `%40` in `.env`.  
**Dev fallback:** `USE_MEMORY_STORE=true` → in-memory conversations only (no Postgres).

`init_db()` on startup runs `create_all` + provider seed if empty.

---

## 8. RAG pipeline (symptoms mode only)

**Indexing (one-off):** `python store_index.py` reads `data/*.pdf`, chunks text, embeds, upserts to Pinecone.

**Runtime:** `src/rag.py`

- `init_rag_chain()` at startup (unless `SKIP_RAG_ON_STARTUP=true`)
- `build_rag_chain()` — Pinecone retriever k=3, Groq chat, system prompt in `src/prompt.py`
- `invoke_rag(user_message)` → answer string

**Env:** `PINECONE_API_KEY`, `GROQ_API_KEY` (required for RAG).

---

## 9. Lab results engine (B6) — detailed

**Not LLM-based.** Flow:

1. `parse_lab_values(text)` in `src/services/lab_parser.py`
   - Parses **line-by-line** (fixes cross-line bugs from PDF tables)
   - Panel regex for: glucose, hemoglobin/hgb, LDL/HDL/total cholesterol, creatinine, TSH, vitamin D
   - Rejects reference-range fragments (e.g. `12.0 - 16.0` misread as result)
   - Unit rules: `g/dL` → hemoglobin; suspicious LDL 10–20 → hemoglobin
2. `interpret_result()` in `src/services/lab_reference.py`
   - Compares value to `reference.min/max` in JSON → `low` | `normal` | `high` | `unknown`
   - Educational `notes` per status
3. `generate_lab_results_reply()` in `src/services/lab_results_service.py` formats bullet list + builds `metadata.lab_results`

**Tests in reference JSON (as of report):** glucose, hemoglobin, total_cholesterol, ldl, hdl, creatinine, tsh, vitamin_d

**Not parsed:** CBC (WBC, RBC, platelets), triglycerides, CMP electrolytes — can be added to `lab_reference.json`.

**Validated with mock report:** Apex Clinical Laboratories style PDF (Jane Doe) — values like TSH 2.1, Hgb 13.8, LDL 138, glucose 108, vitamin D 22 ng/mL match after parser fixes.

---

## 10. Mental health engine (B5)

- Prompt: `src/prompts/mental_health.py`
- Crisis detection: `src/services/crisis_detector.py` (keywords + patterns)
- Non-crisis: `invoke_mental_health_chat()` via Groq (`src/mental_health_llm.py`)
- Optional RAG: `PINECONE_MENTAL_HEALTH_INDEX_NAME` → `src/mental_health_rag.py`
- Crisis response skips LLM; returns helpline metadata (988, Crisis Text Line, 911)

---

## 11. Appointment engine (B4)

- Providers in DB from `data/providers_seed.json` (3 demo providers)
- Chat: `generate_appointment_reply()` lists providers; “book” intent creates hold
- REST: `GET /api/providers`, `POST /api/appointments`
- Held slots mark provider `available: false` in listings

---

## 12. Frontend structure

```
frontend/
  src/
    pages/ChatPage.tsx       # Main shell
    hooks/useChat.ts         # API state, sendMessage, attachFile
    api/
      client.ts              # apiRequest, apiFormRequest
      conversations.ts       # REST wrappers
      types.ts               # DTOs + metadata types
    components/
      chat/                  # Composer, MessageList, QuickActionGrid, Welcome
      layout/                # AppShell, Sidebar, ChatHeader
    constants/quickActions.ts  # Four modes + starter messages
```

**Dev:** `npm run dev` → http://localhost:5173 (Vite proxies `/api` to 8080)  
**Prod:** `npm run build` → `frontend/dist/` served by FastAPI on http://localhost:8080

**Attach button:** PDF/TXT only; uploads in lab_results mode trigger interpretation.

---

## 13. Backend source layout (key files)

```
app.py                          # Entry: create_app()
src/app_factory.py              # FastAPI app, lifespan, routes, CORS
src/frontend_static.py          # SPA serving (Phase 4)
src/config.py                   # Settings from env
src/rag.py                      # Symptoms RAG chain
src/prompt.py                   # RAG system prompt
src/helper.py                   # PDF load, embeddings download
store_index.py                  # One-off Pinecone indexing
src/mock/router.py              # /api/conversations*, mock/status
src/mock/schemas.py             # Pydantic REST DTOs + metadata models
src/services/chat_service.py    # Central mode routing
src/services/lab_results_service.py
src/services/lab_parser.py
src/services/lab_reference.py
src/services/appointment_service.py
src/services/mental_health_service.py
src/services/attachment_service.py
src/persistence/conversation_store.py
src/db/models.py, session.py, seed.py
src/api/appointments_router.py
src/api/attachments_router.py
tests/                          # pytest (61+ tests)
```

**Legacy (still present):** `templates/chat.html`, `POST /api/chat` — used when `frontend/dist` missing.

---

## 14. Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `PINECONE_API_KEY` | Yes (for symptoms / optional MH RAG) | Pinecone |
| `GROQ_API_KEY` | Yes (for symptoms, mental health) | Groq LLM |
| `DATABASE_URL` | Yes (unless `USE_MEMORY_STORE=true`) | PostgreSQL |
| `CORS_ORIGINS` | No | Default includes localhost:5173 |
| `SKIP_RAG_ON_STARTUP` | No | Skip heavy RAG init at boot |
| `USE_MEMORY_STORE` | No | In-memory conversations only |
| `PINECONE_MENTAL_HEALTH_INDEX_NAME` | No | Second index for MH RAG |
| `MENTAL_HEALTH_TEMPERATURE` | No | Default 0.4 |
| `FRONTEND_DIST` | No | Override path to built SPA |
| `SERVE_FRONTEND` | No | Force/warn on missing dist |
| `HUGGINGFACE_API_KEY` | Optional | May be in .env for embeddings hub |

**Never commit `.env`** — contains secrets.

---

## 15. How to run (developer)

### First-time setup

```bash
pip install -r requirements.txt
# Create DB: CREATE DATABASE mediassist;
# .env with PINECONE_API_KEY, GROQ_API_KEY, DATABASE_URL
python store_index.py   # Index Medical_book.pdf to Pinecone
```

### Production-style (one port)

```bash
cd frontend && npm install && npm run build && cd ..
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
# → http://localhost:8080
```

### Dev (hot reload UI)

```bash
# Terminal 1: uvicorn on 8080
# Terminal 2: cd frontend && npm run dev  → http://localhost:5173
```

### Tests

```bash
pip install -r requirements-dev.txt
pytest   # 61 tests
```

---

## 16. Deployment (Render) — planned

- **Build command:** `pip install -r requirements.txt && cd frontend && npm install && npm run build`
- **Start command:** `uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1`
- **Procfile:** `web: uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1`
- Need hosted PostgreSQL `DATABASE_URL` on Render
- Pinecone index must exist (run `store_index.py` locally first)
- Consider `SKIP_RAG_ON_STARTUP=true` on free tier until B7 lazy-load

---

## 17. Implementation phases — completion status

### Frontend (`docs/FRONTEND_PLAN.md`)

| Phase | Status | Summary |
|-------|--------|---------|
| 1 UI shell | Done | MediAssist layout, components |
| 2 REST wiring | Done | React ↔ FastAPI |
| 3 Upload | Done | PDF/TXT attachments, lab mode |
| 4 Production build | Done | `frontend/dist` served by FastAPI |
| 5 Real backends | Mostly done on API | UI metadata display optional |

### Backend (`docs/BACKEND_PLAN.md`)

| Phase | Status | Summary |
|-------|--------|---------|
| B1 Foundation | Mostly done | Tests exist; CI pytest checkbox open |
| B2 Service layer | Done | Mode routing |
| B3 PostgreSQL | Done | Conversations + messages |
| B4 Appointments | Done | Providers + holds |
| B5 Mental health | Done | Crisis + Groq + optional RAG |
| B6 Lab results | Done | Parser + JSON reference + upload |
| B7 Production hardening | **Not done** | Rate limits, lazy RAG, logging, feature flags |

---

## 18. Known limitations and design choices

1. **Educational only** — no diagnosis; lab flags use generic reference ranges, not patient-specific lab printouts.
2. **Lab parsing is regex** — fails on scanned/image PDFs; only text-based PDF and `.txt`.
3. **No image OCR** — user must use text PDF or type values.
4. **Symptoms mode depends on RAG startup** — heavy memory (embeddings model); may fail on small cloud instances without B7.
5. **Partial lab panel** — not all tests on a full CMP/CBC/lipid panel are in `lab_reference.json`.
6. **Appointment booking is mock** — “held” slots, not real scheduling.
7. **Crisis flow is not a crisis counselor** — static resources only.
8. **`.env` URL encoding** — special characters in Postgres password break `DATABASE_URL` if not encoded.
9. **Upload files stored on disk** — `data/uploads/` not in git; not cloud-durable without external storage on deploy.

---

## 19. Recent bugs fixed (context for AI assistants)

| Issue | Cause | Fix |
|-------|-------|-----|
| Postgres `could not translate host name "402911@localhost"` | `@` in password not URL-encoded in `DATABASE_URL` | Use `%40`; save `.env` to disk |
| LDL 12 mg/dL instead of 138 | PDF table extract + cross-line regex; reference range 12.0 confused with Hgb | Line-by-line parser, panel regex, unit heuristics |
| TSH 22 instead of 2.1 | Vitamin D `22 ng/mL` matched across lines to TSH | Line-by-line parse; exclude spurious matches |
| `/health` returned HTML | SPA catch-all registered before `/health` | Register SPA routes last |
| Unsaved `.env` in editor vs disk | Cursor buffer ≠ file on disk | Save file; `load_dotenv(override=True)` |

---

## 20. Suggested next work (roadmap)

1. **Deploy to Render** with hosted Postgres + build frontend in CI/build step  
2. **B7 production hardening** — lazy RAG, rate limiting, logging  
3. **UI polish** — render `metadata.lab_results` and crisis helplines in chat bubbles  
4. **Expand `lab_reference.json`** — triglycerides, WBC, RBC, etc.  
5. **GitHub Actions** — run `pytest` on push  

---

## 21. One-paragraph elevator pitch

MediAssist is an educational medical chatbot that combines a Pinecone–Groq RAG pipeline for encyclopedia-based symptom Q&A with specialized rule-based and LLM-assisted modes for appointments, mental health (including crisis resource detection), and lab-result interpretation from typed text or uploaded PDF lab reports. A React frontend talks to a FastAPI backend backed by PostgreSQL, and the production build is served as a single-page application from the same server as the API, suitable for local development or cloud deployment on Render.

---

*Report generated from codebase state after Frontend Phase 4 and Backend Phases B2–B6. For living plans see `docs/BACKEND_PLAN.md` and `docs/FRONTEND_PLAN.md`.*
