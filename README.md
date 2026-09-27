# Doc Clarity — GenAI Document Intelligence Platform

**Doc Clarity** is an enterprise-grade GenAI document intelligence platform designed to process complex documents across three primary domains:
* **Legal** (Contracts, NDA, Compliance)
* **Insurance** (Policies, Claims)
* **Medical** (Medical reports, Patient records)

---

## Phase 4 Architecture — RAG Pipeline & Gemini LLM Integration

Phase 4 introduces **Document-Grounded Retrieval Augmented Generation (RAG) with Google Gemini LLM**, prompt injection protection, context size control, and source citation traceability.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React 18 + Vite + Tailwind CSS)         │
│  Dashboard UI ──► Ask AI ──► Grounded Q&A Drawer ──► Citation Highlights    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP REST API (Axios)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI API Layer)                       │
│  POST /documents/upload │ POST /{id}/search │ POST /{id}/ask (RAG Endpoint) │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Service Injection
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DOCUMENT-GROUNDED RAG PIPELINE                        │
│                                                                             │
│   1. Document Isolation ──► Validate Status & Filter ChromaDB (document_id) │
│   2. Vector Retrieval   ──► RetrievalService (BAAI/bge-small-en-v1.5)      │
│   3. Prompt Builder     ──► RAGPromptBuilder (Grounding & Injection Guard)  │
│   4. LLM Generation     ──► GeminiLLMService (Google GenAI + Fallbacks)     │
│   5. Response Formatter ──► Citations Mapping & Confidence Heuristics        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration (`.env`)

Add the following environment variables to `backend/.env`:

```env
# Phase 4: RAG & LLM Configuration
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODELS=gemini-2.0-flash,gemini-1.5-flash,gemini-1.5-pro
GEMINI_TEMPERATURE=0.1
GEMINI_MAX_OUTPUT_TOKENS=1000

DEFAULT_RAG_TOP_K=5
MAX_RAG_TOP_K=10
MAX_CONTEXT_CHARS=12000
```

---

## Setup & Running Instructions

### 1. Database Migrations
Run Alembic database migrations:

```bash
cd backend
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

alembic upgrade head
```

### 2. Start Backend API
```bash
uvicorn app.main:app --reload --port 8000
```
Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Start Frontend Dashboard
```bash
cd frontend
npm run dev
```
Dashboard: [http://localhost:3000](http://localhost:3000)

---

## Running Test Suite

Run full automated pytest suite (34 unit & integration tests covering Phases 1–4):

```bash
cd backend
$env:PYTHONPATH="backend"; venv/Scripts/pytest tests/ -v
```

---

## Phase 4 API Specifications

| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/documents/upload` | Upload, extract, chunk, and automatically index embeddings | `201 Created` |
| `GET` | `/api/v1/documents` | List user documents with processing & vector indexing status | `200 OK` |
| `GET` | `/api/v1/documents/{id}` | Inspect metadata details | `200 OK` / `404` |
| `POST` | `/api/v1/documents/{id}/process` | Reprocess text extraction, chunking, and vector indexing | `200 OK` |
| `POST` | `/api/v1/documents/{id}/index` | Re-index vector embeddings into ChromaDB | `200 OK` |
| `GET` | `/api/v1/documents/{id}/index-status` | Get vector index status, chunk count, and model name | `200 OK` |
| `POST` | `/api/v1/documents/{id}/search` | Perform document-isolated semantic similarity search | `200 OK` |
| `POST` | `/api/v1/documents/{id}/ask` | Ask a grounded question about a specific document (RAG + Gemini) | `200 OK` / `400` / `404` / `409` |
| `GET` | `/api/v1/documents/{id}/chunks` | Inspect generated semantic chunks ordered by `chunk_index` | `200 OK` |
| `DELETE` | `/api/v1/documents/{id}` | Delete file, DB chunks, and ChromaDB vector points | `200 OK` / `404` |
