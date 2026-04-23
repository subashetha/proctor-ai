# 🎓 ProctorAI — Online Exam Proctoring System

> **Submitted by:** AI Intern  
> **Organization:** [aumne.ai](https://aumne.ai)  
> **Role:** AI Intern — RAG, LLM Applications, AI System Design  
> **Challenge:** Intern Coding Challenge #19 — Online Exam Proctoring System

---

## 📌 Overview

ProctorAI is a full-stack AI-assisted online exam proctoring system. It automatically detects cheating behavior using a custom proctoring engine, exposes a standards-compliant REST API (FastAPI + OpenAPI), provides a React-based candidate interface, and includes an auto-generated Python SDK.

```
┌────────────────────────────────────────────────────────┐
│                     ProctorAI Stack                    │
│                                                        │
│  React Frontend (port 3000)                            │
│       │  Axios API calls                               │
│       ▼                                                │
│  FastAPI Backend (port 8000)                           │
│       │  SQLAlchemy ORM                                │
│       ▼                                                │
│  SQLite Database  ←  Alembic Migrations                │
│                                                        │
│  Python SDK (generated via OpenAPI Generator CLI)      │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (Windows)

### 1. Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.10+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| npm | 9+ | (bundled with Node.js) |

### 2. Setup

```bat
setupdev.bat
```

This will:
- Create Python virtual environment
- Install all backend dependencies
- Run Alembic database migrations
- Seed the SQLite database with test data
- Install all frontend npm packages

### 3. Run

```bat
runapplication.bat
```

This opens two terminal windows (backend + frontend) and launches the app:

| Service | URL |
|---------|-----|
| Frontend (React) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## 🗂️ Project Structure

```
aumne-proctoring/
├── backend/
│   ├── main.py              # FastAPI app — all endpoints
│   ├── database.py          # SQLAlchemy engine + session
│   ├── models.py            # ORM models (Exam, Submission)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── proctoring.py        # 🤖 AI cheating detection engine
│   ├── seed_data.sql        # Initial test data
│   ├── requirements.txt     # Python dependencies
│   ├── alembic.ini          # Alembic configuration
│   ├── migrations/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 0001_initial.py   # Initial schema migration
│   └── tests/
│       └── test_main.py     # 15+ unit tests
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx          # Root component + navigation
│       ├── App.css          # Dark theme design system
│       ├── main.jsx         # React entry point
│       ├── api/
│       │   └── client.js    # Axios API client
│       └── components/
│           ├── Dashboard.jsx   # KPI cards, flag table, bar chart
│           ├── ExamList.jsx    # Browse available exams
│           ├── TakeExam.jsx    # Timed exam with paste detection
│           └── CreateExam.jsx  # Admin: create new exams
│
├── sdk_usage/
│   ├── demo.py              # SDK/API demonstration script
│   └── README.md            # SDK generation instructions
│
├── setupdev.bat             # One-click environment setup
├── runapplication.bat       # One-click application start
└── README.md                # This file
```

---

## 🔌 API Reference

### Exams

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/exams/` | Create a new exam |
| `GET` | `/exams/` | List all exams |
| `GET` | `/exams/{id}` | Get exam by ID |

**Create Exam — Request Body:**
```json
{
  "title": "Python Fundamentals",
  "duration": 60
}
```

### Submissions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/exams/{id}/submit` | Submit answers (proctoring runs here) |
| `GET` | `/submissions/` | List all submissions (`?flagged_only=true`) |
| `GET` | `/submissions/{id}` | Get submission by ID |

**Submit Exam — Request Body:**
```json
{
  "user_name": "alice",
  "answers": {
    "q1": "Supervised learning uses labeled data...",
    "q2": "def reverse(head): ..."
  },
  "time_taken_seconds": 2100,
  "paste_detected": false
}
```

**Submit Exam — Response:**
```json
{
  "id": 1,
  "exam_id": 1,
  "user_name": "alice",
  "suspicious": true,
  "flag_reasons": ["COPY_PASTE_DETECTED"],
  "time_taken_seconds": 2100
}
```

---

## 🦙 Ollama Setup (Local LLM — Free)

This project uses **Ollama** to run a local LLM for semantic similarity detection. No API key required, runs entirely on your machine.

### Install Ollama
Download from https://ollama.com/download (Windows/Mac) or run: `curl -fsSL https://ollama.com/install.sh | sh` (Linux)

### Pull a model
```bash
ollama pull llama3    # recommended (~4GB)
ollama pull phi3      # lighter option (~2GB)
```

### Start the server
```bash
ollama serve
```

> **Graceful fallback:** If Ollama is not running, the system automatically falls back to rule-based detection. No crash, no error for the user.

---

## 🤖 Proctoring Engine

The AI cheating detection engine (`proctoring.py`) runs on every submission and checks for 5 anomaly types:

| Flag Code | Detection Method | Trigger Condition |
|-----------|-----------------|------------------|
| `COPY_PASTE_DETECTED` | Rule-based | Frontend paste event OR identical answers |
| `BLANK_SUBMISSION` | Rule-based | All answers are empty/whitespace |
| `SUSPICIOUSLY_FAST_SUBMISSION` | Rule-based | Time taken < 20% of allotted exam time |
| `LONG_INACTIVITY_OR_OVERTIME` | Rule-based | Time taken > 110% of allotted exam time |
| `FOCUS_LOSS_DETECTED` | Browser JS | 3+ tab switches or window blur events |
| `AI_SEMANTIC_SIMILARITY_DETECTED` | 🦙 Ollama LLM | Answers are ≥80% semantically similar (catches paraphrasing) |

**Example — Copy-Paste Detection (Backend):**
```python
# These two identical answers trigger COPY_PASTE_DETECTED automatically:
answers = {
  "q1": "def foo(): pass",
  "q2": "def foo(): pass"   # ← identical → flagged
}
```

**Example — Fast Submit:**
```python
# Exam duration = 60 min (3600s), threshold = 20% = 720s
# time_taken_seconds = 30 → SUSPICIOUSLY_FAST_SUBMISSION
```

---

## 🗃️ Database Schema

```sql
CREATE TABLE exams (
    id       INTEGER PRIMARY KEY,
    title    TEXT    NOT NULL,
    duration INT     NOT NULL   -- minutes
);

CREATE TABLE submissions (
    id           INTEGER PRIMARY KEY,
    exam_id      INT     NOT NULL REFERENCES exams(id),
    user_name    TEXT    NOT NULL,
    suspicious   BOOLEAN DEFAULT FALSE,
    flag_reasons TEXT,          -- comma-separated flag codes
    time_taken   INT,           -- seconds
    answers      TEXT           -- serialized answer dict
);
```

Migrations are managed via **Alembic**. To create a new migration:

```bash
cd backend
alembic revision --autogenerate -m "your change description"
alembic upgrade head
```

---

## 🧪 Running Tests

```bash
cd backend
call env\Scripts\activate        # Windows
# source env/bin/activate        # Mac/Linux

pytest tests/ -v
```

**Test coverage includes:**
- Exam CRUD (create, list, get, 404)
- Clean submission accepted
- Copy-paste via frontend flag → flagged
- Copy-paste via identical answers → flagged
- Fast submission → flagged
- Overtime submission → flagged
- Blank submission → flagged
- Non-existent exam → 404
- Empty username → 422
- Flagged-only filter works

---

## 🛠️ SDK Generation

```bash
# Install the generator
npm install -g @openapitools/openapi-generator-cli

# Generate Python SDK (backend must be running)
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o exam_sdk

# Install
pip install -e exam_sdk/
```

**Generated SDK usage:**
```python
from exam_sdk.api.exams_api import ExamsApi
from exam_sdk import ApiClient

client = ApiClient()
api = ExamsApi(client)

# Create exam
exam = api.create_exam_exams_post({"title": "Test", "duration": 60})

# Submit with proctoring
result = api.submit_exam_exams_id_submit_post(exam.id, {
    "user_name": "alice",
    "answers": {"q1": "my answer"},
    "time_taken_seconds": 1800,
    "paste_detected": False
})
print(result.suspicious, result.flag_reasons)
```

Run the demo script:
```bash
python sdk_usage/demo.py
```

---

## 🌟 Bonus Features Implemented

| Feature | Details |
|---------|---------|
| **Real-time Dashboard** | Polls `/submissions/` every 5 seconds for live updates |
| **Bar Chart** | Flag breakdown chart on dashboard |
| **Paste Detection** | Browser-level `onPaste` event captured per question |
| **Tab-Switch Detection** | `visibilitychange` + `blur` events track every focus loss in real time |
| **Timer UI** | Live countdown with color warning (orange < 5min, red < 2min) |
| **OpenAPI Swagger** | Full interactive API docs at `/docs` |
| **Dual Detection** | Frontend paste events AND backend identical-answer comparison |
| **🦙 LLM Semantic Similarity** | Ollama (local, free) detects paraphrased cheating — no API key needed |
| **🤖 AI Audit Log** | LLM writes a plain-English explanation for every flagged submission |
| **Graceful Fallback** | If Ollama is offline, system silently uses rule-based detection only |

---

## 📦 Dependencies

### Backend
```
fastapi       — REST API framework
uvicorn       — ASGI server
sqlalchemy    — ORM
alembic       — DB migrations
pydantic      — Data validation
pytest        — Testing
httpx         — Async test client
```

### Frontend
```
react         — UI framework
axios         — HTTP client
vite          — Build tool
```

---

## 📝 Notes

- Docker is **not** used per challenge requirements
- Frontend communicates **only** via REST API (no direct DB access)
- All API errors return appropriate 4xx/5xx with descriptive messages
- SQLite database file: `backend/proctoring.db`

---

*Built with 💙 by AI Intern @ [aumne.ai](https://aumne.ai)*
