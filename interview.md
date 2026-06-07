# Resume Analyzer — Interview Guide

## One-liner pitch
*"I built a full-stack web app where users upload resumes, get AI-powered scoring and feedback, and can chat with a career coach bot."*

---

## Key talking points (pick 3-4)

1. **Full-stack with Python** — FastAPI backend + Streamlit frontend, PostgreSQL database. Shows you can build end-to-end.

2. **AI integration** — Connected to Groq API (LLaMA 3.3) to parse resumes and generate scores. *"I learned how to work with external APIs, handle prompt engineering, and process JSON responses."*

3. **Authentication** — Implemented JWT-based login/signup with access + refresh tokens, bcrypt password hashing, session management. *"I understand how authentication flows work in a real app."*

4. **Clean architecture** — Used repository pattern, service layer, dependency injection. *"I structured the code to be maintainable and testable — separate concerns between routes, services, and data access."*

5. **Docker** — Containerized with docker-compose (PostgreSQL + backend + frontend). *"I learned containerization for consistent dev/deploy environments."*

---

## How to handle "but someone else could have written this"

Be honest: *"I built this to learn FastAPI and proper backend patterns. The AI calls are through an API — I didn't train a model. What I'm proud of is the architecture: clean separation of concerns, transaction management, and a working auth system. It taught me how real web apps go from idea to deployment."*

---

## What to emphasize as a junior

- **You learned** FastAPI, SQLAlchemy, JWT auth from scratch
- **You made design decisions** (why repository pattern? why Streamlit?)
- **You handled edge cases** (token refresh, PDF parsing fallback, error handling)
- **You shipped something real** — it works end-to-end with Docker

---

## Sample answer to "Tell me about a project"

> *"I built a Resume Analyzer — a web app where you upload a PDF resume and it gets scored across categories like ATS compatibility, skills, and experience. The backend is FastAPI with PostgreSQL, and it uses the Groq API to parse and analyze resumes with LLaMA. I implemented JWT authentication, a chatbot that knows your resume context, and structured the code using repository and service patterns. I Dockerized everything so it runs with one command. The hardest part was getting the AI prompts to return consistent JSON, and managing database transactions properly during API calls."*

---

## Tech Stack Justification

| Layer | Choice | Why |
|---|---|---|
| Framework | **FastAPI** | Async support, auto-docs, Pydantic validation built-in |
| ORM | **SQLAlchemy 2.0** | Mature, repository pattern friendly, raw SQL when needed |
| Auth | **JWT (PyJWT) + bcrypt (passlib)** | Stateless, no session store needed |
| AI | **Groq API (LLaMA 3.3 70B)** | Free, fast inference, no GPU needed |
| Frontend | **Streamlit** | Python-only, fast prototyping |
| DB | **PostgreSQL 15** | JSON fields for parsed resume data |
| Deploy | **Docker + docker-compose** | 3 services: postgres + backend + frontend |

---

## Architecture: Layered (5 layers)

```
Route (endpoints) → Service (business logic) → Repository (data access) → Model (ORM) → DB
                                     ↕
                          Dependency Injection (AppSession)
```

**1. Routes layer** (`app/routes/`) — Thin, just validates request -> calls service -> returns response

**2. Services layer** (`app/services/`) — All business logic: auth flows, AI calls, transaction management

**3. Repositories layer** (`app/repositories/`) — Pure DB queries, no business logic

**4. Models** (`app/database/models.py`) — SQLAlchemy ORM: 6 tables (User, UserSession, Resume, ResumeAnalysis, ChatSession, ChatMessage)

**5. Dependencies** (`app/dependencies/`) — FastAPI dependency injection: DB session per request, auth extraction

---

## Feature Deep Dives

### Feature 1: Authentication (JWT with access + refresh tokens)

**Flow:**
1. `POST /auth/signup` — bcrypt hash, store user, return ID
2. `POST /auth/login` — verify password -> create JWT access token (24h) + refresh token (7d) -> store refresh token hashed in `user_sessions` table -> set both as cookies + return in body
3. `POST /auth/refresh` — read refresh cookie -> verify JWT -> check session not revoked/expired -> issue new access token
4. `POST /auth/logout` — revoke the session in DB, clear cookies

**Key design decisions:**
- Refresh tokens are **hashed with SHA-256** before DB storage (so a DB leak doesn't expose valid tokens)
- Sessions table tracks `user_agent` and `ip_address` — enables future "log out other devices" feature
- `AppSession.set_user(user_id)` is **immutable** — prevents accidental identity switching

### Feature 2: Resume Upload & AI Parsing

**Flow:**
1. `POST /resumes/upload` — accepts PDF or `.txt`
2. **PDF extraction**: tries `pdfplumber` first, **falls back to `pypdf`** (graceful degradation)
3. **AI parsing**: sends raw text to Groq with a system prompt that enforces structured JSON output
4. Parsed JSON written back to `resumes` table (skills, experience, education, certs, languages as JSON columns)

**Smart design choice**: AI call is done **outside the DB transaction** — you don't hold a DB connection/transaction open during network I/O. Then a second transaction writes the results. This avoids long-lived transactions and connection pool starvation.

### Feature 3: AI Analysis + Job Matching

- `POST /resumes/analyse` — takes `resume_id` + optional `job_description`
- Sends structured resume context + JD to Groq
- Returns 6 scores (overall, ATS, skills, experience, education, formatting) + strengths/weaknesses/suggestions/keyword matches
- **Error handling**: if AI call fails, returns a default "retry" analysis instead of crashing

### Feature 4: AI Career Coach Chat

**Flow:**
1. `POST /chat/` — sends user message + resume context + last 20 messages as history
2. `_detect_intent()` — keyword-based router that classifies the question (analysis_query, improvement, skills_advice, job_advice, salary_info, interview_prep, cover_letter)
3. System prompt enforces topic boundaries — refuses off-topic questions
4. Uses `asyncio.to_thread()` so the blocking Groq call doesn't block FastAPI's async event loop

---

## Database Schema (6 Tables)

```sql
users              -- id, email, hashed_password, full_name, is_active, created_at
user_sessions      -- id, user_id, refresh_token (hashed), status, expires_at, revoked_at, user_agent, ip_address
resumes            -- id, user_id, filename, raw_text, candidate_name, email, phone, ... + JSON columns
resume_analyses    -- id, resume_id, job_description, analysis_type, 6 score columns, JSON feedback columns
chat_sessions      -- id (UUID), user_id, created_at
chat_messages      -- id, session_id, user_id, role, content, resume_id
```

---

## Design Patterns Used

1. **Repository Pattern** — `BaseRepository` with generic `create`, `update`, `delete`, `get_by_id`, `get_one`, `list`. Concrete repos extend it. Data access logic is isolated.

2. **Service Layer Pattern** — `BaseService` abstract class provides `self.session`, `self.repository`, `self.get_db_session()`. Each service is a single unit of business logic.

3. **Dependency Injection** — `AppSessionDep` is a FastAPI dependency that creates one `AppSession` per request. `CurrentUserDep` extracts the authenticated user.

4. **Savepoint-based Transactions** — `DatabaseSessionWrapper.transaction()` uses nested savepoints. Depth 1 = main transaction. Depth 2+ = SAVEPOINT, so partial failures roll back only the inner block.

5. **AI Prompt Engineering** — System prompts enforce strict JSON output. The parser strips markdown fence markers with regex before `json.loads()`.

---

## Common Interview Q&A

### Q: Why FastAPI and not Django?

> "I chose FastAPI because it's lighter — automatic OpenAPI docs, Pydantic validation built-in, async support. Django would be overkill for this: I don't need an admin panel, ORM is already handled by SQLAlchemy, and I wanted to learn the request-response cycle without Django's abstraction layer. It was a deliberate learning choice."

### Q: Why are you using Streamlit instead of React?

> "Streamlit let me prototype the full app in Python alone — I'm a backend-focused developer and didn't want to spend weeks learning React for a portfolio project. It proved the concept worked. If this went to production, I'd rebuild the frontend in React/Next.js."

### Q: How would you scale this?

> "Three bottlenecks: the AI API call, the database, and file uploads. For AI, I'd move analysis to a background worker (Celery + Redis) so the API doesn't block. For the DB, I'd add connection pooling tuning and read replicas. For uploads, I'd stream files directly to S3 instead of keeping them in memory with `file.read()`."

### Q: Explain the transaction management in detail

> "Every write operation uses `with self.get_db_session():` context manager. Inside, `DatabaseSessionWrapper` handles savepoints — the first call uses the main transaction, nested calls create SAVEPOINTs so a failure in an inner operation only rolls back the inner block, not the whole request. The context commits on success, rolls back on exception, and re-raises. The AI call in `create_and_parse` happens *between* two transactions — we don't hold a DB connection during the network call."

### Q: What about security? Any vulnerabilities you know of?

> "What I did right: bcrypt for passwords, SHA-256 hashing for stored refresh tokens, JWT with expiration, session tracking with revocation. What I'd add: rate limiting on auth endpoints, CORS restricted to specific origins (currently `allow_origins=["*"]`), HTTPS enforcement, proper CSRF protection for cookie-based auth, and input sanitization before sending to the AI."

### Q: How does the resume parsing work end-to-end?

> "User uploads PDF -> `_extract_text_from_upload()` reads the bytes. For PDFs, it tries pdfplumber first (better text extraction), falls back to pypdf if that fails. For text files, tries UTF-8 then latin-1. The raw text is saved immediately to DB. Then a separate AI call sends it to LLaMA 3.3 with a system prompt that enforces structured JSON output — I strip markdown fences with regex before parsing. AI result is saved in a second transaction."

### Q: Did you write tests? Why only auth tests?

> "I wrote 4 auth tests covering signup, duplicate email, login, and wrong password. This was my first time writing pytest tests with FastAPI's TestClient. I'd add tests for resume upload and analysis next — mocking the Groq API so tests don't require real API calls."

### Q: How do you handle the Groq API being down or returning bad data?

> "Two failure modes: (1) Parsing failure — returns an empty dict, so the resume is saved without parsed fields and the user sees partial data. (2) Analysis failure — catches the exception and returns a default analysis with scores of 0 and a 'please retry' message. The LLM sometimes returns markdown-wrapped JSON or invalid JSON — I handle that with regex stripping and try/except around `json.loads()`."

### Q: What's the difference between your AppSession and a raw SQLAlchemy Session?

> "AppSession wraps a raw Session and adds: immutable user identity (set once, can't be changed — prevents bugs), lifecycle hooks (pre/post commit for audit logs), consistent error handling on add/flush/commit that auto-rollbacks on failure, and typed helper methods. It's a thin adapter that keeps the repository code cleaner."

### Q: Can you walk through the auth flow step by step?

> "Signup: validate input -> check email not taken -> bcrypt hash password -> insert User row -> return success.
>
> Login: find user -> verify password -> check active -> create access token (24h, HS256, contains user_id + email + token_type='access') -> create refresh token (7d) -> hash the refresh token with SHA-256 -> store in user_sessions table with user_agent and IP -> set both as cookies -> return tokens.
>
> Refresh: read refresh cookie -> verify JWT -> check session in DB isn't revoked or expired -> fetch user -> issue new access token -> update cookie.
>
> Logout: revoke session in DB -> clear cookies."

### Q: How would you add pagination to the resume list?

> "The `BaseRepository.list()` currently filters but doesn't paginate. I'd add `page` and `limit` query params to the route, add `offset = (page - 1) * limit` to the query, and include `PaginationInfo` from my existing `base.py` in the response — count, total_count, page, limit. The `ApiListResponse` generic is already set up for this."

### Q: One thing you'd refactor immediately?

> "The `_extract_text_from_upload()` function lives in the route file — it should be in a utility module or a dedicated service. I'd also move the AI system prompts out of `resume_service.py` into config files or a prompts module so they're easier to iterate on without touching code."

---

---

## Common Junior Interview Questions — At a Glance

| Question | How the project answers it |
|---|---|
| Explain JWT auth | Access + refresh tokens, bcrypt hashing, session tracking with revocation |
| How do you handle errors? | HTTPException with status codes, fallback AI responses, DB rollback on failure |
| How do you structure a Python project? | 5-layer architecture: routes → services → repositories → models → DB |
| How do you handle file uploads? | PDF parsing with pdfplumber + pypdf fallback, encoding fallbacks for txt |
| How do you secure a REST API? | JWT in Authorization header + cookie, bcrypt passwords, refresh token hashing |
| What's dependency injection? | FastAPI Depends + AppSession per request |
| How do you handle database transactions? | Context manager with commit/rollback, savepoints for nesting |
| How do you work with AI APIs? | Prompt engineering for structured JSON output, error handling for unreliability |
| What testing have you done? | pytest + TestClient for auth endpoints, fixture-based test DB |

---

## What to Say When They Ask "What Would You Improve?"

- Add **rate limiting** to AI endpoints
- Add **pagination** to resume list endpoint
- Add **email verification** flow
- Move AI prompts to separate config files
- Add **async database** with asyncpg for true async DB access
- Add **background task queue** (Celery/Redis) for AI analysis so the API doesn't block
- Add **comprehensive test suite** with mocked external API calls
