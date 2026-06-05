# Medical Chatbot

RAG-based medical Q&A web app (FastAPI + Pinecone + Groq). For educational use only — not a substitute for professional medical advice.

## Prerequisites

- **Python 3.11 or 3.12** recommended (see `runtime.txt`). Python 3.13 works if `numpy>=2` wheels install cleanly.
- **PostgreSQL** running locally (or remote) for conversation persistence (Phase B3).
- `.env` with:
  - `PINECONE_API_KEY`
  - `GROQ_API_KEY`
  - `DATABASE_URL` (example below)

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/mediassist
```

Create the database once:

```sql
CREATE DATABASE mediassist;
```

## Setup

```bash
git clone https://github.com/Sahil2927/Medical_Chatbot.git
cd Medical_Chatbot
conda create -n medibot python=3.11 -y
conda activate medibot
pip install -r requirements.txt
```

## Index PDFs (first time / after corpus changes)

Place PDFs in `data/`, then:

```bash
python store_index.py
```

## Run locally

**API (FastAPI):**

```bash
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

**MediAssist UI (Phase 1 — React):**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 (proxies `/api` to port 8080).

**Production UI (Phase 4 — single server):**

```bash
cd frontend
npm install
npm run build
cd ..
uvicorn app:app --host 0.0.0.0 --port 8080
```

Open http://localhost:8080 (MediAssist React app + API on one port). Requires `frontend/dist/` from `npm run build`.

**Run both for local dev (hot reload):**

```bash
# terminal 1
uvicorn app:app --host 0.0.0.0 --port 8080 --reload

# terminal 2
cd frontend && npm run dev
```

Mock API docs: http://localhost:8080/docs (tag: MediAssist Mock API).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Backend roadmap: `docs/BACKEND_PLAN.md`.

**Optional:** `USE_MEMORY_STORE=true` skips PostgreSQL (in-memory only, data lost on restart).

Legacy Jinja chat (only when `frontend/dist/` is missing): http://localhost:8080/

- MediAssist React UI: `/` (after `npm run build`)
- JSON API: `POST /api/chat` with body `{"msg": "your question"}`
- Health: `GET /health`
- API docs: http://localhost:8080/docs

## Deploy (Render)

1. **New Web Service** (not Blueprint) → connect this repo.
2. **Build:** `pip install -r requirements.txt && cd frontend && npm install && npm run build`
3. **Start:** `uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1`
4. Set environment variables `PINECONE_API_KEY`, `GROQ_API_KEY`, `DATABASE_URL`, etc.
5. Ensure Pinecone index `medical-chatbot` exists (run `store_index.py` locally first).
6. Open the service URL — MediAssist UI is served from `frontend/dist/` on the same host.

## Troubleshooting

**`DeprecatedPluginError: pinecone-plugin-inference`**

```bash
pip uninstall pinecone-plugin-inference -y
pip install -r requirements.txt
```

**`NumPy requires GCC >= 8.4` during `pip install`**

Pip tried to build old NumPy from source (common on Python 3.13). Use the pinned `requirements.txt` (includes `numpy>=2.1`) or switch to Python 3.11:

```bash
conda create -n medibot python=3.11 -y
conda activate medibot
pip install -r requirements.txt
```
