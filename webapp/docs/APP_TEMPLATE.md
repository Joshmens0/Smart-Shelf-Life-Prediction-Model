# Universal App Template — Architecture, Standards & Rules
## Mandatory Reference for All Applications Built in This Workspace

> **For AI Agents & Developers:** Read this document in full before creating, modifying, or extending any application. Every rule defined here is non-negotiable and applies universally.

---

## 0. First Principles (Always Active)

1. **Never take shortcuts.** Fix problems for the long term, not the current moment.
2. **Always use the most optimized and secure implementation.** Best practices only — no quick fixes.
3. **Write clean, readable, modular code.** Every file, function, and class has exactly one responsibility.
4. **Never leave behind unused imports, variables, dead code, or TODO stubs in production.**
5. **Always update documentation** (`docs/`, `README.md`, or relevant `.md` files) after any code change.
6. **Validate → Evaluate → Implement → Test → Document → Proceed.** Never skip a step.

---

## 1. Technology Stack (Locked Choices)

### Backend
| Layer | Choice |
|---|---|
| API Framework | **FastAPI** (Python 3.12+) |
| ORM | **SQLAlchemy 2** (async with `asyncpg` for production, `aiosqlite` for tests) |
| Database | **PostgreSQL** (production) / **SQLite** (testing/dev) |
| Schema Migrations | **Alembic** — always version-controlled, never edited retroactively |
| Cache & Locks | **Redis** — rate limiting, session locks, distributed state |
| Input Validation | **Pydantic v2** — strict mode, all API request/response shapes |
| Linting | **Ruff** — enforced before every commit, zero warnings allowed |
| Testing | **Pytest** with `pytest-asyncio` strict mode — all tests async |

### Frontend
| Layer | Choice |
|---|---|
| Framework | **React 18+** with **TypeScript** |
| Build Tool | **Vite** |
| Styling | **Vanilla CSS** + CSS Tokens (`tokens.css`) |
| Testing | **Vitest** + **React Testing Library** |
| Error Handling | **React Error Boundary** (`<ErrorBoundary />`) |
| Fonts | Google Fonts (Inter, Outfit) |

### Infrastructure
| Layer | Choice |
|---|---|
| Reverse Proxy | **Nginx** (TLS termination, rate limit zones, HSTS headers) |
| Container | **Docker** + **Docker Compose** |
| CI/CD | **GitHub Actions** (lint → test → build → validate) |
| Secrets | Environment variables via `.env` — never committed |
| Backups | Automated shell scripts (`backup.sh`) with retention pruning |
