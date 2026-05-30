# Resume Analyser AI

An AI-powered tool that reads your resume, scores it, and tells you what to fix. Also comes with an AI career coach chatbot for more interactive advice.

I built this to learn FastAPI + SQLAlchemy properly, and it turned into a full-ish app. Uses LLaMA 3.3 70B via the Groq API (which is free and fast, honestly impressive).

---

## What it does

- **Upload a resume** (PDF or .txt) and it auto-extracts everything — name, skills, experience, education, certs, languages
- **AI analysis** with scores out of 100: overall, ATS, skills, experience, education, formatting
- **Job description matching** — paste a JD and it tells you which keywords you hit and what you're missing
- **Actionable suggestions** specific to your resume, not generic advice
- **AI career coach** — a chatbot that knows your resume and answers questions about it
- **User accounts** with JWT auth so your resumes and chat history persist between visits
- **Chat sessions** stored server-side, organised per conversation

## Tech stack

| Layer | What I used |
|-------|-------------|
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| AI | LLaMA 3.3 70B via Groq API |
| Database | PostgreSQL 15 |
| Frontend | Streamlit |
| Auth | JWT (PyJWT) + bcrypt (passlib) |
| PDF parsing | pdfplumber (falls back to pypdf) |
| Containers | Docker, docker-compose |

## Project structure

```
resume_analyzer/
├── .env
├── .gitignore
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.frontend
│
├── app/
│   ├── main.py
│   ├── core/
│   │   └── config.py                  # loads env vars via Pydantic Settings
│   ├── database/
│   │   ├── session.py                 # SQLAlchemy engine + session
│   │   └── models.py                  # all ORM models
│   ├── models/
│   │   └── schemas.py                 # Pydantic request/response models
│   ├── base/
│   │   ├── base.py                    # declarative base
│   │   ├── base_repository.py         # generic CRUD
│   │   ├── base_service.py            # abstract service
│   │   └── database_session.py        # commit/rollback context manager
│   ├── repositories/
│   │   ├── user_repository.py         # user CRUD only
│   │   ├── user_session.py            # session CRUD (revoke, mark_expired)
│   │   └── resume_repository.py       # resumes, analyses, chat messages
│   ├── services/
│   │   ├── auth_service.py            # signup, login, logout, refresh
│   │   ├── token_service.py           # JWT create + verify
│   │   ├── user_session.py            # session logic (token hashing)
│   │   ├── resume_service.py          # AI parsing + scoring
│   │   └── chat_service.py            # AI career coach
│   ├── dependencies/
│   │   └── auth_dependency.py         # get_current_user
│   └── routes/
│       ├── auth.py
│       ├── resume.py
│       └── chat.py
│
├── frontend/
│   ├── main.py
│   ├── config/
│   │   ├── settings.py
│   │   └── styles.py                  # custom CSS (way too much of it)
│   ├── pages/
│   │   ├── auth_page.py
│   │   └── main_page.py
│   ├── components/
│   │   ├── score_card.py
│   │   └── sidebar.py
│   └── utils/
│       ├── api_client.py              # http client with auto token refresh
│       └── session.py                 # streamlit session state management
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

pip install -r requirements.txt
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
| POST | `/resumes/upload` | Upload PDF/TXT, auto-parse with AI |
| GET | `/resumes/` | List all your resumes |
| GET | `/resumes/{id}` | Get resume details |
| DELETE | `/resumes/{id}` | Delete a resume |
| POST | `/resumes/analyse` | Run AI analysis (optional job description) |
| GET | `/resumes/{id}/analyses` | List analyses for a resume |

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

1. Signup — password gets bcrypt hashed, stored in the users table.
2. Login — verify password, generate access token (24h) + refresh token (7d). Refresh token gets SHA-256 hashed and saved in user_sessions. Both tokens go into HTTP cookies.
3. Every API call — `get_current_user()` reads the Bearer token, verifies the JWT, checks the user exists and is active.
4. On 401 — frontend auto-calls `/auth/refresh` using the refresh cookie, gets a new access token, retries the original request.
5. Logout — session is revoked in the DB (status = "revoked"), cookies are cleared.
6. Natural expiry — when a refresh token's JWT expires, the session is marked "expired" (not revoked). This is a different status so you can tell the difference between "user logged out" and "token ran out".

Access token lives in Streamlit session state (in-memory). Refresh token gets stored as a browser cookie via JavaScript.

## What I learned building this

- Pydantic v2 with `model_config` instead of the old `Config` class
- Why you'd separate repositories from services (initially I had everything in one file, got messy fast)
- That session management is more involved than I expected — distinguishing revoked vs expired, hashing tokens before storing them, etc.
- Groq's API is genuinely fast for an LLM, and free tier is generous
- Streamlit is quick to build with but custom CSS is painful at scale
- SQLAlchemy 2.0 style (`select()` instead of `Query`) feels cleaner once you get used to it
- Putting curl in a Docker image just for a healthcheck feels wrong but it works
- I should have written more tests from the start

## Things I'd add if I kept going

- Pagination on resumes and chat history
- WebSocket streaming for the chatbot so it doesn't feel as slow
- More tests (auth is covered, basically nothing else is)
- CI pipeline with GitHub Actions
- .docx support
- Email verification
- Rate limiting on auth endpoints
- An admin panel would be nice but that's a whole other project

---

*Built as a portfolio project while learning FastAPI, Docker, and actually structuring a backend properly.*
