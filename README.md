# GovAssist-RAG

GovAssist-RAG is a multimodal assistant for discovering Indian government schemes. It combines a FastAPI backend, a LangGraph orchestration flow, Sarvam-powered language services, SQLite persistence, local or remote Qdrant retrieval, and a Next.js frontend.

The current runtime supports:

- Text chat for scheme discovery
- Audio upload and in-browser voice recording
- PDF and image document extraction
- Query translation into English for retrieval and answer localization back to the user language
- Streamed responses over NDJSON
- Chat session persistence in SQLite
- Scheme scraping and re-indexing
- Optional Twilio WhatsApp webhook handling

## Architecture

### Active request flow

1. A request reaches the FastAPI app through `POST /chat`, `POST /chat/stream`, or the Twilio webhook.
2. The API normalizes the input:
   - `application/json` for text chat
   - `multipart/form-data` for document and audio chat
   - audio is transcribed with Sarvam
   - non-English text is translated to `en-IN` for retrieval
3. A LangGraph state machine runs:
   - `MainAgent` decides whether to answer directly, extract a document, or retrieve schemes
   - `DocumentAgent` extracts text from PDFs or images
   - `LLMAgent` handles direct assistant replies and post-retrieval synthesis
   - `RAGAgent` retrieves schemes from Qdrant, with SQLite keyword fallback
4. The API returns either a blocking response or streamed chunks plus a final payload.
5. The frontend stores session history in SQLite via the backend session APIs.

### Core modules

- [main.py](/home/navs-15/GovAssist-RAG/main.py)
- [govassist/api/api.py](/home/navs-15/GovAssist-RAG/govassist/api/api.py)
- [govassist/agents/graph.py](/home/navs-15/GovAssist-RAG/govassist/agents/graph.py)
- [govassist/agents/nodes.py](/home/navs-15/GovAssist-RAG/govassist/agents/nodes.py)
- [govassist/api/db_utils.py](/home/navs-15/GovAssist-RAG/govassist/api/db_utils.py)
- [govassist/rag/vector_store.py](/home/navs-15/GovAssist-RAG/govassist/rag/vector_store.py)
- [frontend/src/app/page.tsx](/home/navs-15/GovAssist-RAG/frontend/src/app/page.tsx)

### Current design notes

- The graph store has been decommissioned; retrieval is Qdrant plus SQLite fallback.
- The live UI is the Next.js app in `frontend/`.
- `govassist/rag/pipeline.py` and parts of the older `govassist/rag/llm.py` path are legacy and are not the main FastAPI runtime path.
- The backend root route serves a lightweight HTML landing page, not the frontend app itself.

## Repository layout

```text
GovAssist-RAG/
├── govassist/
│   ├── agents/        # LangGraph state, nodes, and graph wiring
│   ├── api/           # FastAPI app, chat/session APIs, SQLite helpers
│   ├── ingestion/     # Playwright-based scraper
│   ├── integrations/  # Sarvam and Twilio clients
│   └── rag/           # embeddings, Qdrant wrapper, legacy modules
├── data/raw/          # scraped scheme JSON
├── frontend/          # Next.js frontend
├── main.py            # backend entrypoint
├── scrape.py          # scrape + optional reindex entrypoint
└── test_graph.py      # simple graph invocation smoke test
```

## Requirements

- Python 3.12+
- Node.js 18+ for the frontend
- `npm`
- Enough local disk/RAM for sentence-transformer embeddings and local Qdrant data

Optional but often needed:

- Playwright browser binaries for scraping
- Twilio credentials for WhatsApp
- A Sarvam API key for real chat, STT, translation, and TTS

## Quick start

If you want the shortest path to a running local app:

1. Create and activate a Python virtual environment.
2. Install backend dependencies.
3. Create a root `.env` file with at least `SARVAM_API_KEY` if you want real AI behavior.
4. Start the backend with `python3 main.py`.
5. In a second terminal, install frontend dependencies in `frontend/`.
6. Start the frontend with `npm run dev`.
7. Open `http://localhost:3000`.

Minimal command sequence:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 main.py
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Then open:

- Frontend: `http://localhost:3000`
- Backend API docs: `http://127.0.0.1:8000/docs`

## Backend setup

Install Python dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the repository root. A practical starting point is:

```env
SARVAM_API_KEY=
SARVAM_CHAT_MODEL=sarvam-m
LOG_LEVEL=INFO

API_HOST=127.0.0.1
API_PORT=8000
API_RELOAD=false
API_BASE_URL=http://127.0.0.1:8000
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

QDRANT_MODE=local
QDRANT_LOCAL_PATH=./qdrant_data
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
FORCE_RECREATE_COLLECTION=false

AUTO_INGEST=true
SCRAPE_OUTPUT_FILE=data/raw/scheme.json
MAX_SCHEMES_PER_CATEGORY=0

TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### Important env notes

- `SARVAM_API_KEY` is required for real Sarvam behavior.
- If `SARVAM_API_KEY` is missing:
  - chat completion falls back to echoing the last user message
  - STT returns a mock transcript
  - translation becomes a pass-through
  - TTS returns a short silent WAV clip
- `QDRANT_MODE=local` stores vectors in `./qdrant_data` and does not require a separate Qdrant server.
- `MAX_SCHEMES_PER_CATEGORY=0` means unlimited during scraping.

## Run locally

### 1. Backend

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set any values you need, especially:

- `SARVAM_API_KEY` for real chat, translation, STT, and TTS
- `QDRANT_MODE=local` if you want to use the built-in local Qdrant storage
- `CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000` for local frontend access

Start the backend:

```bash
source .venv/bin/activate
python3 main.py
```

Expected result:

- FastAPI starts on `http://127.0.0.1:8000`
- Swagger docs are available at `http://127.0.0.1:8000/docs`
- The app creates SQLite databases on startup if they do not already exist

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
```

Set the frontend API base URL if needed:

```bash
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Then start the frontend:

```bash
npm run dev
```

Expected result:

- Next.js starts on `http://localhost:3000`
- The UI can call the backend at `http://127.0.0.1:8000`

### 3. Optional: refresh scheme data

If you want to scrape fresh scheme data instead of using the existing local data:

```bash
source .venv/bin/activate
playwright install
python3 scrape.py
```

Expected result:

- scraped scheme JSON is written to `data/raw/scheme.json`
- scheme rows are inserted into SQLite
- Qdrant indexes are refreshed when `AUTO_INGEST=true`

### 4. Sanity-check the app

After both servers are running, verify with:

1. Open `http://127.0.0.1:8000/health` and confirm it returns `{"status":"ok"}`.
2. Open `http://127.0.0.1:8000/docs` and confirm the API schema loads.
3. Open `http://localhost:3000`.
4. Send a text query such as `schemes for women farmers in Telangana`.

## Run the backend

```bash
source .venv/bin/activate
python3 main.py
```

The API will start on `http://127.0.0.1:8000` unless overridden by `API_HOST` and `API_PORT`.

Useful endpoints:

- `GET /`
- `GET /health`
- `POST /chat`
- `POST /chat/stream`
- `POST /tts`
- `GET /api/sessions`
- `GET /api/sessions/{session_id}`
- `POST /api/sessions`
- `DELETE /api/sessions/{session_id}`
- `POST /scrape`
- `POST /webhook/twilio`

Swagger docs are available at `http://127.0.0.1:8000/docs`.

## Frontend setup

Install and run the Next.js app:

```bash
cd frontend
npm install
npm run dev
```

Frontend environment:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

The frontend runs on `http://localhost:3000` by default.

### Frontend behavior

The current UI supports:

- session history
- streamed assistant replies
- text input
- microphone recording with `MediaRecorder`
- document upload
- per-message TTS playback
- light/dark theme toggle
- a WhatsApp onboarding modal

Current implementation note:

- The WhatsApp join code and number are hardcoded in [frontend/src/app/page.tsx](/home/navs-15/GovAssist-RAG/frontend/src/app/page.tsx) rather than sourced from env vars.

## Chat input modes

### Text

Send JSON:

```json
{
  "query": "Schemes for women farmers in Telangana",
  "session_id": "web-demo"
}
```

### Audio

Send `multipart/form-data` with an audio file field such as `audio_file` or `voice_file`.

### Document

Send `multipart/form-data` with:

- `file` containing a PDF or image
- optional `query`
- optional `audio_file` if the user wants to pair a voice query with the document

Supported document suffixes:

- `.pdf`
- `.png`
- `.jpg`
- `.jpeg`
- `.webp`
- `.bmp`
- `.tiff`
- `.tif`

Supported audio suffixes:

- `.mp3`
- `.wav`
- `.m4a`
- `.ogg`
- `.aac`
- `.flac`

## Data and indexing

### SQLite

- [govassist/api/schemes.db](/home/navs-15/GovAssist-RAG/govassist/api/schemes.db): normalized scheme catalog
- [govassist/api/chat_history.db](/home/navs-15/GovAssist-RAG/govassist/api/chat_history.db): saved chat sessions

### Raw data

- [data/raw/scheme.json](/home/navs-15/GovAssist-RAG/data/raw/scheme.json)
- [data/raw/schemes.json](/home/navs-15/GovAssist-RAG/data/raw/schemes.json)

The scraper writes to `data/raw/scheme.json` by default. The active retrieval/indexing path is based on SQLite plus Qdrant, not direct JSON reads at request time.

### Qdrant

- Local Qdrant data is stored in `qdrant_data/` when `QDRANT_MODE=local`.
- During ingestion, scheme text is embedded with `BAAI/bge-small-en-v1.5`.
- If Qdrant retrieval fails, the app falls back to SQLite keyword scoring.

## Scraping and reindexing

Run the scraping pipeline manually:

```bash
source .venv/bin/activate
python3 scrape.py
```

What it does:

1. Scrapes selected category pages from `myscheme.gov.in` using Playwright
2. Writes normalized scheme records to `data/raw/scheme.json`
3. Refreshes SQLite/Qdrant indexes if `AUTO_INGEST=true`

The API also exposes `POST /scrape`, which starts the scraper in the background.

If you use the scraper, install Playwright browser binaries first:

```bash
playwright install
```

If you only want to use the project without re-scraping, you can skip this step and work with the data already present in the repo and local databases.

## WhatsApp integration

The backend includes a Twilio webhook at `POST /webhook/twilio`.

Behavior:

- Twilio sends inbound text or media to the webhook
- the backend acknowledges immediately with empty TwiML
- full processing runs in the background
- replies are sent back using Twilio’s REST API

Required env vars for real WhatsApp sending:

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_NUMBER`

## Testing and verification

There is a lightweight graph smoke test:

```bash
source .venv/bin/activate
python3 test_graph.py
```

This is not a full automated test suite; it mainly checks that the graph can be invoked with a simple state payload.

## Known limitations

- Scheme-query detection is mostly keyword-based before retrieval.
- The graph store and true synergy retrieval are currently retired, even though related response fields still exist in state/output.
- The frontend WhatsApp values are hardcoded.
- Some legacy files remain in the repo and can be confused with the live runtime path.
- Scraping depends on the current structure of `myscheme.gov.in` and may require selector updates over time.
- Running with no Sarvam credentials is suitable for local wiring checks, not real assistant quality.

## Recommended local workflow

1. Start the backend with a configured `.env`.
2. Start the frontend from `frontend/`.
3. If scheme data is stale, run `python3 scrape.py`.
4. Verify indexing by testing a scheme query through `/chat` or the web UI.

## Reference docs in the repo

- [PROJECT_AUDIT.md](/home/navs-15/GovAssist-RAG/PROJECT_AUDIT.md)
- [SCRAPE_INDEXING_REPORT.md](/home/navs-15/GovAssist-RAG/SCRAPE_INDEXING_REPORT.md)
- [govassist_architecture.md.resolved](/home/navs-15/GovAssist-RAG/govassist_architecture.md.resolved)
