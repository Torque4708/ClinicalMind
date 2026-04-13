# 🧬 ClinicalMind
### AI Clinical Trial Intelligence & Patient Matching Engine

ClinicalMind is a production-grade SaaS platform where doctors or patients describe a medical condition in plain English, and the system semantically matches them to real active clinical trials from ClinicalTrials.gov using LLMs, vector search, and RAG.

---

## 🚀 Key Features

| Feature | Technology |
|---------|-----------|
| Medical Entity Extraction | LangChain + Groq (llama3-70b-8192) |
| Semantic Trial Matching | pgvector cosine similarity |
| Eligibility Explanation | LangChain Agent with 3 tools |
| RAG Chat over Trials | LangChain + pgvector retrieval |
| Background ETL | Celery Beat (every 6 hours) |
| Authentication | JWT + bcrypt |
| Frontend | Streamlit multi-page app |
| Infrastructure | Docker + PostgreSQL + Redis |

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────┐
│  Streamlit UI   │────▶│  FastAPI Backend      │────▶│  PostgreSQL │
│  (port 8501)    │     │  (port 8000)          │     │  + pgvector │
└─────────────────┘     └──────────────────────┘     └─────────────┘
                                  │                          │
                         ┌────────▼─────────┐      ┌────────▼────────┐
                         │  Celery Worker   │      │  Groq API       │
                         │  + Beat Scheduler│      │  llama3-70b     │
                         └────────┬─────────┘      └─────────────────┘
                                  │
                         ┌────────▼─────────┐
                         │  Redis (broker)  │
                         └──────────────────┘
```

---

## ⚡ Quick Start

### 1. Clone and Configure
```bash
git clone <repo-url>
cd ClinicalMind
cp .env.example .env
```

Edit `.env` and set your **GROQ_API_KEY** and a strong **SECRET_KEY**:
```
GROQ_API_KEY=gsk_your_key_here
SECRET_KEY=your-32-char-secret-key-here
```

### 2. Launch with Docker Compose
```bash
docker compose up --build -d
```

This starts 6 services:
- **postgres** — PostgreSQL 15 with pgvector (port 5432)
- **redis** — Redis 7 (port 6379)
- **backend** — FastAPI app (port 8000)
- **celery_worker** — Processes ETL tasks
- **celery_beat** — Schedules ETL every 6 hours
- **frontend** — Streamlit UI (port 8501)

### 3. Access the App
| Service | URL |
|---------|-----|
| Streamlit Frontend | http://localhost:8501 |
| FastAPI Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

### 4. Initial Data Load
The ETL pipeline runs automatically on startup. To trigger a manual sync:
1. Register an **admin** account via the UI
2. Navigate to **Admin** panel → **Trigger Manual Sync**

Or via API:
```bash
curl -X POST http://localhost:8000/trials/sync \
  -H "Authorization: Bearer <your_admin_token>"
```

---

## 🔧 Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL locally (with pgvector) and Redis

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/clinicalmind"
export GROQ_API_KEY="your_key"
export SECRET_KEY="your_secret"
export REDIS_URL="redis://localhost:6379/0"

# Run backend
uvicorn backend.main:app --reload

# Run Celery worker (new terminal)
celery -A backend.tasks.etl_tasks.celery_app worker --loglevel=info

# Run frontend (new terminal)
streamlit run frontend/streamlit_app.py
```

---

## 📁 Project Structure

```
ClinicalMind/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Pydantic settings from .env
│   ├── database.py          # Async SQLAlchemy + pgvector init
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic v2 request/response schemas
│   ├── routers/             # FastAPI route handlers
│   │   ├── auth.py          # Register, login, /me
│   │   ├── profile.py       # Patient profile CRUD
│   │   ├── match.py         # Trial matching + eligibility agent
│   │   ├── chat.py          # RAG chat endpoint
│   │   └── trials.py        # Trial listing, stats, admin sync
│   ├── services/            # Business logic
│   │   ├── auth_service.py  # bcrypt password management
│   │   ├── entity_extractor.py  # LangChain entity extraction
│   │   ├── trial_fetcher.py     # ClinicalTrials.gov API client
│   │   ├── embedder.py          # sentence-transformers (384-dim)
│   │   ├── matcher.py           # pgvector cosine search
│   │   ├── rag_service.py       # RAG retrieval + LLM answer
│   │   └── agent_service.py     # LangChain tool-calling agent
│   ├── tasks/
│   │   └── etl_tasks.py     # Celery tasks + beat schedule
│   └── utils/
│       └── jwt_utils.py     # JWT creation + FastAPI dependencies
├── frontend/
│   └── streamlit_app.py     # Multi-page Streamlit UI
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🛠️ API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create user account |
| POST | `/auth/login` | Get JWT token |
| GET | `/auth/me` | Current user info |

### Patient Profiles
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/profile/` | Create profile + auto-extract entities |
| GET | `/profile/{id}` | Get profile by ID |
| GET | `/profile/my/all` | All profiles for current user |

### Trial Matching
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/match/` | Semantic match to top-k trials |
| POST | `/match/explain` | Agent eligibility explanation |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat/` | RAG-grounded Q&A over trial docs |

### Trials
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/trials/` | Paginated trial list |
| GET | `/trials/{nct_id}` | Single trial details |
| GET | `/trials/stats` | Stats and phase distribution |
| POST | `/trials/sync` | Admin: trigger ETL sync |

---

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | asyncpg PostgreSQL connection string |
| `GROQ_API_KEY` | Groq API key (get from console.groq.com) |
| `SECRET_KEY` | JWT signing secret (min 32 chars) |
| `REDIS_URL` | Redis connection URL |
| `CELERY_BROKER_URL` | Celery broker (Redis) |
| `CELERY_RESULT_BACKEND` | Celery result backend (Redis) |
| `JWT_ALGORITHM` | JWT algorithm (default: HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL (default: 60) |

---

## 📄 License

MIT License — Built using FastAPI, LangChain, Groq, pgvector, and Streamlit.
