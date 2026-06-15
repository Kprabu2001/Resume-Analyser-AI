# Resume Analyser AI

An AI-powered tool that reads your resume, scores it, and tells you what to fix. Also comes with an AI career coach chatbot for more interactive advice.

Built with FastAPI + SQLAlchemy on the backend, Streamlit on the frontend, and LLaMA 3.3 70B via the Groq API.

---

## What it does

| Feature | Description |
|---------|-------------|
| **Upload & Parse** | Upload PDF, DOCX, or TXT — AI extracts name, skills, experience, education, certs, languages. Magic byte validation detects file type by content, not extension. |
| **AI Analysis** | Scores out of 100: overall, ATS, skills, experience, education, formatting — with actionable suggestions |
| **Job Description Matching** | Paste a JD and it tells you which keywords you hit and what you're missing |
| **Cover Letter Generator** | Generate a tailored cover letter from your resume + JD, with configurable tone |
| **PDF Report Export** | Download any analysis as a PDF report |
| **AI Career Coach** | Chatbot that knows your resume and answers career questions |
| **User Accounts** | JWT auth with access/refresh token rotation — resumes and chat history persist |

## Tech stack

| Layer | What I used |
|-------|-------------|
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| AI | LLaMA 3.3 70B via Groq API |
| Database | PostgreSQL 15 |
| Frontend | Streamlit |
| Auth | JWT (PyJWT) + bcrypt (passlib) |
| File parsing | pdfplumber, pypdf, python-docx |
| PDF export | fpdf2 |
| Container | Docker, docker-compose |

## Project structure

```
resume_analyzer/
├── .env
├── .gitignore
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.frontend
│
├── app/
│   ├── main.py                         # app entry, logging setup, lifespan
│   ├── core/
│   │   └── config.py                   # Pydantic Settings (env vars)
│   ├── database/
│   │   ├── session.py                  # sync SQLAlchemy engine + session
│   │   └── models.py                   # ORM models (string PKs)
│   ├── models/
│   │   └── schemas.py                  # Pydantic request/response models
│   ├── base/
│   │   ├── base.py                     # declarative base + AppBase mixin
│   │   ├── server.py                   # AppServer (FastAPI subclass) with auth middleware, request ID logging
│   │   ├── id_gen.py                   # generate_id(prefix) utility
│   │   ├── log_context.py              # thread-local request_id context
│   │   ├── log_formatter.py            # RequestIdFormatter for log messages
│   │   ├── base_repository.py          # generic CRUD with FilterNode system
│   │   ├── base_service.py             # abstract service base
│   │   ├── app_session.py              # sync wrapper around sqlalchemy.orm.Session
│   │   └── database_session.py         # context manager with savepoint support
│   ├── utils/
│   │   ├── file_validator.py           # magic byte detection + DOCX extraction
│   │   └── pdf_export.py               # fpdf2 analysis report generator
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── user_session.py
│   │   └── resume_repository.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── token_service.py
│   │   ├── user_session.py
│   │   ├── resume_service.py           # AI parsing, analysis, cover letter generation
│   │   └── chat_service.py
│   ├── dependencies/
│   │   ├── auth_dependency.py          # CurrentUserIdDep — reads request.state.user_id
│   │   └── db_dependency.py            # AppSessionDep
│   └── routes/
│       ├── auth.py
│       ├── resume.py
│       └── chat.py
│
├── frontend/
│   ├── main.py
│   ├── .streamlit/config.toml          # maxUploadSize = 5
│   ├── config/
│   │   ├── settings.py
│   │   └── styles.py                   # custom CSS
│   ├── pages/
│   │   ├── auth_page.py
│   │   └── main_page.py
│   ├── components/
│   │   ├── score_card.py
│   │   └── sidebar.py
│   └── utils/
│       ├── api_client.py               # HTTP client with auto token refresh
│       └── session.py                  # Streamlit session state management
│
└── tests/
    └── test_auth.py
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

# Option B: everything together
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

## API endpoints

### Auth — `/auth`

| Method | Path | What |
|--------|------|------|
| POST | `/auth/signup` | Create account (full_name, email, password) |
| POST | `/auth/login` | Login, get JWT tokens (access + refresh in cookies) |
| POST | `/auth/logout` | Revoke session, clear cookies |
| POST | `/auth/refresh` | Refresh access token using refresh cookie |

### Resumes — `/resumes` (auth required)

| Method | Path | What |
|--------|------|------|
| POST | `/resumes/upload` | Upload PDF/DOCX/TXT, auto-parse with AI |
| GET | `/resumes/` | List all your resumes |
| GET | `/resumes/{id}` | Get resume details |
| DELETE | `/resumes/{id}` | Delete a resume |
| POST | `/resumes/analyse` | Run AI analysis (optional job description) |
| GET | `/resumes/{id}/analyses` | List analyses for a resume |
| POST | `/resumes/cover-letter` | Generate tailored cover letter (tone, company, JD) |
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
| GET | `/health` | Health check (status, service, version) |

## How auth works

1. **Signup** — password gets bcrypt hashed, stored in the users table.
2. **Login** — verify password, generate access token (24h) + refresh token (7d). Refresh token gets SHA-256 hashed and saved in `user_sessions`.
3. **Middleware-based auth** — `AppServer._request_middleware` intercepts every request. For non-public paths, it extracts the JWT from `Authorization: Bearer` header (or `ACCESS_COOKIE` fallback), verifies it via `TokenService`, and sets `request.state.user_id`. Returns 401 immediately if invalid.
4. **Route-level dependency** — `CurrentUserIdDep` reads `request.state.user_id` and returns it as a `str`. No extra DB query per request.
5. **On 401** — frontend auto-calls `/auth/refresh` using the refresh cookie, gets a new access token, retries the original request.
6. **Logout** — session is revoked in the DB (status = "revoked"), cookies are cleared.

Access token lives in Streamlit session state (in-memory). Refresh token gets stored as a browser cookie via JavaScript.

## Request logging

Every request gets a unique `X-Request-ID` (generated or propagated from client). All log messages during a request are automatically tagged with a short request ID in brackets:

```
INFO app.base.server - [af493fc54eb7] GET /resumes/ - Request started
INFO app.base.server - [af493fc54eb7] GET /resumes/ - 200 in 7.13ms
```

This follows a thread-local context pattern (inspired by voiez-backend) — no need to pass `request_id` around manually.

## What I learned building this

- Pydantic v2 with `model_config` instead of the old `Config` class
- Why you'd separate repositories from services (initially I had everything in one file, got messy fast)
- That session management is more involved than I expected — distinguishing revoked vs expired, hashing tokens before storing them, etc.
- Groq's API is genuinely fast for an LLM, and free tier is generous
- Streamlit is quick to build with but custom CSS is painful at scale
- SQLAlchemy 2.0 style (`select()` instead of `Query`) feels cleaner once you get used to it
- Magic byte file validation is trivial to implement and catches real mislabeled uploads
- fpdf2 is surprisingly capable for pure-Python PDF generation
- Moving auth to middleware avoids repeating the same logic in every route

## Things I'd add if I kept going

- Pagination on resumes and chat history
- WebSocket streaming for the chatbot so it doesn't feel as slow
- More tests (auth is covered, basically nothing else is)
- CI pipeline with GitHub Actions
- Email verification
- Rate limiting on auth endpoints
- An admin panel would be nice but that's a whole other project

---

*Built as a portfolio project while learning FastAPI, Docker, and actually structuring a backend properly.*
