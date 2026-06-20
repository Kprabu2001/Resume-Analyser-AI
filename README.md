# Resume Analyser AI

Upload a resume, get it parsed, scored, and critiqued by AI. Also generates cover letters, exports PDF reports, and has a chatbot that actually knows what's on your resume.

Built with FastAPI + SQLAlchemy on the backend, Streamlit on the frontend, and LLaMA 3.3 70B via the Groq API.

---

## What it does

| Feature | Description |
|---------|-------------|
| **Upload & Parse** | PDF, DOCX, or TXT — AI extracts name, skills, experience, education, certs, languages. Magic byte validation catches mislabeled files. |
| **AI Analysis** | Scored out of 100 across overall, ATS compatibility, skills, experience, education, formatting — with specific suggestions for each |
| **Job Description Matching** | Paste a job description and it tells you which keywords you matched and what's missing |
| **Cover Letter Generator** | Writes a tailored cover letter from your resume + JD. Adjustable tone, company name, hiring manager. |
| **PDF Report Export** | Download any analysis as a formatted PDF |
| **AI Career Coach** | Chatbot that's aware of your resume and answers career questions. Won't write poems for you (it tries, I had to add refusal training). |
| **User Accounts** | JWT auth with access/refresh token rotation. Your resumes and chat history are yours. |
| **DOCX Support** | Upload .docx files alongside PDF and TXT |

## Tech stack

| Layer | What I used |
|-------|-------------|
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| AI | LLaMA 3.3 70B via Groq API (direct SDK, no LangChain) |
| Database | PostgreSQL 15 |
| Frontend | Streamlit |
| Auth | JWT (PyJWT) + bcrypt (passlib) |
| File parsing | pdfplumber, pypdf, python-docx |
| PDF export | fpdf2 |
| Container | Docker, docker-compose |
| Deploy | Render (backend), Streamlit Cloud (frontend), Supabase (DB) |

## Project structure

```
resume_analyzer/
├── .env.example
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.frontend
├── render.yaml
│
├── app/
│   ├── main.py                         # app entry, logging setup, lifespan
│   ├── core/
│   │   └── config.py                   # Pydantic Settings from env vars
│   ├── database/
│   │   ├── session.py                  # sync SQLAlchemy engine + session factory
│   │   └── models.py                   # 6 ORM models (string PKs with prefixes)
│   ├── models/
│   │   └── schemas.py                  # Pydantic request/response models
│   ├── base/
│   │   ├── base.py                     # declarative base + filter node system
│   │   ├── server.py                   # AppServer (FastAPI subclass) — auth middleware, request IDs
│   │   ├── id_gen.py                   # generate_id("USR") → "USR_aB3xK9..."
│   │   ├── log_context.py              # thread-local request ID context
│   │   ├── log_formatter.py            # [request_id] in every log line
│   │   ├── base_repository.py          # generic CRUD with FilterNode dynamic queries
│   │   ├── base_service.py             # abstract service with session management
│   │   ├── app_session.py              # sync wrapper around sqlalchemy.orm.Session
│   │   ├── database_session.py         # context manager with savepoint support
│   │   └── constants.py                # cookie name constants
│   ├── utils/
│   │   ├── file_validator.py           # magic byte detection + DOCX extraction
│   │   ├── groq_client.py              # Groq SDK wrapper with tenacity retry
│   │   └── pdf_export.py               # fpdf2 analysis report generator
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── user_session.py
│   │   └── resume_repository.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── token_service.py
│   │   ├── user_session.py
│   │   ├── resume_service.py           # AI parsing, analysis, cover letters
│   │   └── chat_service.py
│   ├── dependencies/
│   │   ├── auth_dependency.py          # CurrentUserIdDep — reads request.state
│   │   └── db_dependency.py            # AppSessionDep
│   └── routes/
│       ├── auth.py
│       ├── resume.py
│       └── chat.py
│
├── frontend/
│   ├── main.py
│   ├── .streamlit/config.toml
│   ├── config/
│   │   ├── settings.py                 # URLs, colors, quick suggestions
│   │   └── styles.py                   # custom CSS
│   ├── pages/
│   │   ├── auth_page.py
│   │   └── main_page.py
│   ├── components/
│   │   ├── score_card.py
│   │   └── sidebar.py
│   └── utils/
│       ├── api_client.py               # HTTP client with auto token refresh
│       └── session.py                  # Streamlit session state + cookie handling
│
└── tests/
    ├── test_auth.py                    # 7 auth tests
    
```

## Quick start

### Prerequisites

- Python 3.11+
- PostgreSQL 15 (or Docker)
- A Groq API key — free at https://console.groq.com

### 1. Clone and install

```bash
git clone <repo-url>
cd resume_analyzer

python -m venv venv
# source venv/bin/activate    (mac/linux)
# venv\Scripts\activate       (windows)

pip install -e .
```

### 2. Set up .env

```bash
cp .env.example .env
```

Edit `.env` with your values:

```
GROQ_API_KEY=gsk_your_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_analyser
SECRET_KEY=<run: python -c "import secrets; print(secrets.token_hex(32))">
DEBUG=False
BACKEND_URL=http://localhost:8000
```

### 3. Start the database

```bash
# Option A: standalone postgres with docker
docker run -d --name resume-pg \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=resume_analyser \
  -p 5432:5432 postgres:15-alpine

# Option B: everything together (postgres + backend + frontend)
docker-compose up --build
```

### 4. Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

- API docs at http://localhost:8000/docs
- Health check at http://localhost:8000/health

### 5. Start the frontend

```bash
cd frontend
streamlit run main.py
```

App runs at http://localhost:8501.

### 6. Run tests

```bash
pytest tests/ -v
```

Requires a test database — the connection string is in `tests/conftest.py`. Tests mock the Groq API so no actual AI calls happen.

## API endpoints

### Auth — `/auth`

| Method | Path | What |
|--------|------|------|
| POST | `/auth/signup` | Create account |
| POST | `/auth/login` | Login, get JWT tokens |
| POST | `/auth/logout` | Revoke session, clear cookies |
| POST | `/auth/refresh` | Refresh access token using refresh cookie |

### Resumes — `/resumes` (auth required)

| Method | Path | What |
|--------|------|------|
| POST | `/resumes/upload` | Upload PDF/DOCX/TXT, auto-parse with AI |
| GET | `/resumes/` | List your resumes |
| GET | `/resumes/{id}` | Resume details |
| DELETE | `/resumes/{id}` | Delete a resume |
| POST | `/resumes/analyse` | Run AI analysis (optional job description) |
| GET | `/resumes/{id}/analyses` | List analyses for a resume |
| POST | `/resumes/cover-letter` | Generate cover letter |
| GET | `/resumes/{id}/analyses/{aid}/export` | Download analysis as PDF |

### Chat — `/chat` (auth required)

| Method | Path | What |
|--------|------|------|
| POST | `/chat/` | Send message to AI career coach |
| DELETE | `/chat/session/{id}` | Clear chat session |
| GET | `/chat/history/{id}` | Get chat history |

### Health

| Method | Path | What |
|--------|------|------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check |

## How auth works

1. **Signup** — password gets bcrypt hashed, stored in `users` table.
2. **Login** — verify password, generate access token (30 min) + refresh token (7 days). Refresh token is SHA-256 hashed before storing in `user_sessions`.
3. **Middleware-based auth** — `AppServer._request_middleware` intercepts every non-public request. It pulls the JWT from `Authorization: Bearer` header (or access cookie as fallback), verifies it, and sets `request.state.user_id`. Invalid tokens get an immediate 401.
4. **Route-level dependency** — `CurrentUserIdDep` reads `request.state.user_id`. No extra DB query needed per request.
5. **On 401** — frontend catches it, calls `/auth/refresh` with the refresh cookie, gets a new access token, retries the original request.
6. **Logout** — session is marked revoked in the DB, cookies are cleared.

Access token lives in Streamlit session state (in-memory). Refresh token is an HTTP-only cookie — JavaScript can't read it.

Tokens are set with `httponly=True`, `samesite="lax"`, and the refresh cookie is scoped to `/auth/refresh` only.

## Request logging

Every request gets a unique ID. All log messages during that request are tagged with it:

```
INFO app.base.server - [af493fc54eb7] GET /resumes/ - Request started
INFO app.base.server - [af493fc54eb7] GET /resumes/ - 200 in 7.13ms
```

Uses Python's `threading.local()` so concurrent requests don't mix up IDs. Pattern taken from voiez-backend.

## Notable quirks and fixes

- **String IDs** — everything uses prefixed random IDs (`USR_`, `RES_`, etc.) instead of auto-increment integers. You can tell what a record is just by looking at its ID. Also more secure — no sequential guessing.
- **No LangChain** — direct Groq SDK calls are simpler and faster for a single-resume-per-request pattern. LangChain would add complexity without benefit at this scale.
- **No RAG** — one resume at a time fits in the prompt context. No need for vector search.
- **fpdf2 for PDFs** — pure Python, zero system dependencies. Keeps the Docker image small.
- **Thread-local logging** — async projects use `contextvars`, but this is a sync app so `threading.local()` works fine.
- **JSON columns** — skills, experience, education are stored as PostgreSQL JSON columns instead of separate join tables. Simpler code, fewer joins.
- **Supabase connection uses the transaction pooler** (port 6543) — the direct connection (port 5432) doesn't work from Render because it's IPv6 only.
- **The refresh cookie is scoped to `/auth/refresh`** — it's only sent when needed, reducing exposure.
- **Access token expiry is 30 minutes** — not 24 hours. Short enough that stolen tokens are limited damage, long enough to not be annoying.
- **The Groq client has retry with exponential backoff** — 3 attempts with 2s → 4s → 8s waits. Only retries on network errors and rate limits.
- **The JSON cleaner (`_clean_json_response()`) strips markdown fences, extracts `{...}` content, and escapes literal newlines inside JSON strings** — LLMs love to add extra text and put real newlines inside string values.

## Things I'd add if I kept going

- WebSocket streaming for the chatbot (the 1-2s wait per message gets old)
- CI pipeline with GitHub Actions (tests run automatically on push)
- Email verification on signup
- Rate limiting on auth endpoints
- Better error messages from the AI when parsing fails (it occasionally returns garbage JSON)
- Pagination on resume list and chat history
- An admin panel would be nice but that's a whole other project

---

*Built as a portfolio project while learning FastAPI, Docker, and actually structuring a backend properly. Yeah, I shipped a bug with the bcrypt version on the first deploy. It happens.*
