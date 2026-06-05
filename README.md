# MediAssist

[![CI](https://github.com/Sahil2927/Medical_Chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/Sahil2927/Medical_Chatbot/actions/workflows/ci.yml)

**MediAssist** is a RAG-powered medical assistant web app that answers health questions using curated knowledge bases. It combines a **React** frontend, **FastAPI** backend, **Pinecone** vector search, **Groq** LLMs, and **PostgreSQL** for conversation history.

**Live demo:** [https://mediassist-rboj.onrender.com](https://mediassist-rboj.onrender.com)

> **Medical disclaimer:** MediAssist provides educational information only. It is **not** a substitute for professional medical advice, diagnosis, or treatment. In an emergency, contact your local emergency services immediately.

---

## Features

| Mode | Description |
|------|-------------|
| **Check Symptoms** | RAG over a medical encyclopedia (`Medical_book.pdf` → Pinecone `medical-chatbot`) |
| **Book Appointment** | Mock provider lookup and appointment booking flow |
| **Mental Health Check-in** | Crisis detection with helpline metadata; Groq chat with optional RAG (`medical-chatbot-mh`) |
| **Review Lab Results** | Hybrid lab parser + reference ranges + optional RAG narrative (`medical-chatbot-lab`) |

Additional capabilities:

- Conversation history persisted in PostgreSQL
- Crisis helpline panels and structured lab-result metadata in the UI
- Rate limiting, request IDs, and lazy RAG initialization for production
- Single-server production build (React `dist/` served by FastAPI)

---

## Tech stack

| Layer | Technologies |
|-------|----------------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI, Uvicorn, SQLAlchemy |
| RAG | LangChain, sentence-transformers (`all-MiniLM-L6-v2`), Pinecone |
| LLM | Groq (`llama-3.1-8b-instant`) |
| Database | PostgreSQL |
| Deploy | Render (Blueprint + `render.yaml`), GitHub Actions CI |

---

## Architecture

```
User → React UI (/) → FastAPI (/api/*)
                          ├── PostgreSQL (conversations, messages)
                          ├── Pinecone (symptoms / MH / lab indexes)
                          └── Groq API (generation)
```

Indexing is done **locally** (or any machine with API keys). The deployed app reads vectors from Pinecone cloud — your laptop does not need to stay on.

---

## Project structure

```
Medical_Chatbot/
├── app.py                  # FastAPI entrypoint
├── src/                    # Backend (RAG, services, API, DB)
├── frontend/               # React MediAssist UI
├── data/
│   ├── Medical_book.pdf    # Symptoms corpus (not committed if large/copyrighted)
│   └── kb/                 # Mental health & lab PDF folders
├── store_index.py          # Index symptoms PDF → medical-chatbot
├── store_index_to_pinecone.py  # Index kb folders → mh / lab indexes
├── render.yaml             # Render Blueprint
├── scripts/render_build.sh # Production build (CPU PyTorch + npm build)
└── tests/                  # pytest suite
```

---

## Prerequisites

- **Python 3.11** (recommended; see `runtime.txt`)
- **Node.js 20** (for frontend dev/build)
- **PostgreSQL** (local or remote)
- API keys: [Pinecone](https://www.pinecone.io/), [Groq](https://console.groq.com/)
- PDF sources for indexing (see [Indexing](#indexing-pinecone))

---

## Environment variables

Create a `.env` file in the project root (never commit it):

```env
PINECONE_API_KEY=your_pinecone_key
GROQ_API_KEY=your_groq_key
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/mediassist

# Optional — defaults shown
PINECONE_MENTAL_HEALTH_INDEX_NAME=medical-chatbot-mh
PINECONE_LAB_RESULTS_INDEX_NAME=medical-chatbot-lab
```

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `PINECONE_API_KEY` | Yes | — | Pinecone access |
| `GROQ_API_KEY` | Yes | — | LLM generation |
| `DATABASE_URL` | Yes* | — | PostgreSQL connection |
| `PINECONE_MENTAL_HEALTH_INDEX_NAME` | No | — | MH RAG index name |
| `PINECONE_LAB_RESULTS_INDEX_NAME` | No | — | Lab RAG index name |
| `LAZY_RAG_INIT` | No | `true` | Defer RAG load until first use |
| `ENVIRONMENT` | No | `development` | `production` disables mock status |
| `USE_MEMORY_STORE` | No | `false` | Skip PostgreSQL (dev only) |

\*Not required if `USE_MEMORY_STORE=true` (data lost on restart).

Symptoms mode uses Pinecone index **`medical-chatbot`** (hardcoded default in `src/config.py`).

Create the local database once:

```sql
CREATE DATABASE mediassist;
```

---

## Setup

```bash
git clone https://github.com/Sahil2927/Medical_Chatbot.git
cd Medical_Chatbot

# Python
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Frontend (dev)
cd frontend && npm install && cd ..
```

---

## Indexing (Pinecone)

Run these from your machine **once** (or after PDF changes). Indexes live in Pinecone cloud and are shared with production.

### 1. Symptoms — `medical-chatbot`

Place `Medical_book.pdf` in `data/`, then:

```bash
python store_index.py
```

### 2. Mental health — `medical-chatbot-mh`

```bash
python store_index_to_pinecone.py --folder data/kb/mental_health --index medical-chatbot-mh
```

### 3. Lab results — `medical-chatbot-lab`

```bash
python store_index_to_pinecone.py --folder data/kb/lab_results --index medical-chatbot-lab
```

Confirm all three indexes exist in the [Pinecone console](https://app.pinecone.io) (384-dim, cosine).

---

## Run locally

### Development (hot reload)

```bash
# Terminal 1 — API
uvicorn app:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2 — UI
cd frontend && npm run dev
```

Open [http://localhost:5173](http://localhost:5173) (Vite proxies `/api` to port 8080).

### Production-style (single server)

```bash
cd frontend && npm run build && cd ..
uvicorn app:app --host 0.0.0.0 --port 8080
```

Open [http://localhost:8080](http://localhost:8080).

### Useful endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | MediAssist UI |
| `GET /health` | `{"status":"ok","rag_ready":bool}` |
| `POST /api/chat` | Legacy symptoms JSON API `{"msg":"..."}` |
| `GET /docs` | OpenAPI (Swagger) |

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

CI runs on every push/PR to `main` via GitHub Actions.

---

## Deploy (Render)

### Blueprint (recommended)

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
2. Connect this repo → apply `render.yaml`
3. When prompted, set **`PINECONE_API_KEY`** and **`GROQ_API_KEY`** (sync: false — set manually in Environment)
4. Wait for deploy; open the service URL

The Blueprint provisions:

- **mediassist** — Python web service (build: `scripts/render_build.sh`)
- **mediassist-db** — PostgreSQL

### Render environment checklist

| Variable | Set in Render? |
|----------|----------------|
| `PINECONE_API_KEY` | Yes — must match the key used for indexing |
| `GROQ_API_KEY` | Yes |
| `DATABASE_URL` | Auto from Blueprint |
| `PINECONE_MENTAL_HEALTH_INDEX_NAME` | `medical-chatbot-mh` (in `render.yaml`) |
| `PINECONE_LAB_RESULTS_INDEX_NAME` | `medical-chatbot-lab` (in `render.yaml`) |

**Notes:**

- First symptoms request downloads the embedding model (~20–40s on free tier).
- Free tier (512 MB) may OOM on RAG cold start — upgrade to **Starter** if needed.
- Free web services sleep after ~15 min idle; first visit after sleep is slow.

---

## Troubleshooting

### `Symptom checking is unavailable until the knowledge base is loaded`

1. Run `python store_index.py` and confirm index `medical-chatbot` has vectors in Pinecone.
2. On Render, verify `PINECONE_API_KEY` is correct (logs: `Invalid API Key` = wrong key).
3. Wait 30–60s on the first symptoms message (lazy RAG + model download).

### `Cannot find module '@/lib/cn'` (build)

Ensure `frontend/src/lib/cn.ts` is tracked in git (not ignored by root `lib/` in `.gitignore`).

### `DeprecatedPluginError: pinecone-plugin-inference`

```bash
pip uninstall pinecone-plugin-inference -y
pip install -r requirements.txt
```

### NumPy build errors on Python 3.13

Use Python 3.11:

```bash
python -m venv .venv --python=3.11
pip install -r requirements.txt
```

---

## Documentation

- [Backend plan](docs/BACKEND_PLAN.md)
- [Frontend plan](docs/FRONTEND_PLAN.md)
- [Project report](docs/PROJECT_REPORT.md)

---

## License

See [LICENSE](LICENSE).

---

## Author

[Sahil2927](https://github.com/Sahil2927)
