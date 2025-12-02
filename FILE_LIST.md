# OpenFyxer - Complete File List

This document contains the complete list of all files included in the OpenFyxer archive.

## Root Directory Files

| File | Description |
|------|-------------|
| `.env.example` | Environment variables template |
| `.gitignore` | Git ignore rules |
| `ARCHITECTURE.md` | System architecture documentation |
| `docker-compose.yml` | Docker Compose configuration for full stack |
| `LICENSE` | MIT License |
| `PLAN.md` | Development plan |
| `README.md` | Project documentation and setup instructions |
| `FILE_LIST.md` | This file - complete archive contents |

## GitHub Actions (`.github/workflows/`)

| File | Description |
|------|-------------|
| `ci.yml` | Continuous Integration workflow |
| `release.yml` | Release automation workflow |

## Backend (`backend/`)

### Main Application Files

| File | Description |
|------|-------------|
| `Dockerfile` | Backend Docker image configuration |
| `pyproject.toml` | Python project configuration and dependencies |
| `poetry.lock` | Locked Python dependencies |

### Application Core (`backend/app/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `main.py` | FastAPI application entry point |

### API Layer (`backend/app/api/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `deps.py` | Dependency injection utilities |

### API v1 Endpoints (`backend/app/api/v1/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `router.py` | API router configuration |

### API v1 Endpoints (`backend/app/api/v1/endpoints/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `audit.py` | Audit logs endpoints |
| `auth.py` | Authentication endpoints (register, login, 2FA) |
| `calendar.py` | Calendar events endpoints |
| `chat.py` | AI Chat endpoints (LLM integration) |
| `drafts.py` | Email drafts endpoints |
| `emails.py` | Email management endpoints |
| `meetings.py` | Meetings and transcription endpoints |
| `rag.py` | RAG/Knowledge Base endpoints |
| `settings.py` | User settings endpoints |
| `users.py` | User management endpoints |

### Core Utilities (`backend/app/core/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `config.py` | Application configuration |
| `encryption.py` | Encryption utilities for OAuth tokens |
| `exceptions.py` | Custom exception classes |
| `security.py` | Password hashing, JWT, 2FA utilities |

### Database (`backend/app/db/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `base.py` | SQLAlchemy base model |
| `session.py` | Database session management |

### Models (`backend/app/models/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `audit_log.py` | Audit log model |
| `calendar_event.py` | Calendar event model |
| `document.py` | Document model for RAG |
| `draft.py` | Email draft model |
| `email.py` | Email model |
| `email_account.py` | Email account model |
| `meeting.py` | Meeting model |
| `user.py` | User model |
| `user_settings.py` | User settings model |

### Schemas (`backend/app/schemas/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `audit.py` | Audit log schemas |
| `calendar.py` | Calendar event schemas |
| `chat.py` | Chat message schemas |
| `draft.py` | Draft schemas |
| `email.py` | Email schemas |
| `meeting.py` | Meeting schemas |
| `rag.py` | RAG query schemas |
| `settings.py` | Settings schemas |
| `user.py` | User schemas (including RegisterResponse) |

### Services (`backend/app/services/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `calendar_service.py` | Calendar integration service |
| `email_service.py` | Email provider integration |
| `llm_service.py` | LLM service (Ollama + cloud providers) |
| `notification_service.py` | Notification service |
| `rag_service.py` | RAG/GraphRAG service |
| `transcription_service.py` | Audio transcription service |

### Workers (`backend/app/workers/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `celery_app.py` | Celery application configuration |

### Worker Tasks (`backend/app/workers/tasks/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `email_tasks.py` | Email processing tasks |
| `notification_tasks.py` | Notification tasks |
| `rag_tasks.py` | RAG indexing tasks |
| `transcription_tasks.py` | Transcription tasks |

### Tests (`backend/tests/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `conftest.py` | Pytest configuration |

### Benchmark Tests (`backend/tests/benchmarks/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `test_performance.py` | Performance benchmark tests |

### Integration Tests (`backend/tests/integration/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `test_api_endpoints.py` | API endpoint tests |
| `test_calendar_flow.py` | Calendar flow tests |
| `test_email_flow.py` | Email flow tests |
| `test_meeting_flow.py` | Meeting flow tests |

### Unit Tests (`backend/tests/unit/`)

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `test_email_classification.py` | Email classification tests |
| `test_prompt_generation.py` | Prompt generation tests |
| `test_rag_integration.py` | RAG integration tests |
| `test_security.py` | Security utilities tests |

## Frontend (`frontend/`)

### Configuration Files

| File | Description |
|------|-------------|
| `.env.example` | Frontend environment variables template |
| `.eslintrc.cjs` | ESLint configuration |
| `Dockerfile` | Frontend Docker image configuration |
| `index.html` | HTML entry point |
| `nginx.conf` | Nginx configuration for production |
| `package.json` | NPM dependencies and scripts |
| `package-lock.json` | Locked NPM dependencies |
| `postcss.config.js` | PostCSS configuration |
| `tailwind.config.js` | Tailwind CSS configuration |
| `tsconfig.json` | TypeScript configuration |
| `tsconfig.node.json` | TypeScript Node configuration |
| `vite.config.ts` | Vite build configuration |
| `vitest.config.ts` | Vitest test configuration |

### Public Assets (`frontend/public/`)

| File | Description |
|------|-------------|
| `favicon.svg` | Application favicon |

### Source Code (`frontend/src/`)

| File | Description |
|------|-------------|
| `App.tsx` | Main React application component |
| `index.css` | Global CSS styles |
| `main.tsx` | Application entry point |
| `vite-env.d.ts` | Vite environment types |

### Components (`frontend/src/components/layout/`)

| File | Description |
|------|-------------|
| `Header.tsx` | Application header component |
| `Layout.tsx` | Main layout wrapper |
| `Sidebar.tsx` | Navigation sidebar component |

### Internationalization (`frontend/src/i18n/`)

| File | Description |
|------|-------------|
| `index.ts` | i18n configuration |

### Locales (`frontend/src/i18n/locales/`)

| File | Description |
|------|-------------|
| `en.json` | English translations |
| `ro.json` | Romanian translations |

### Pages (`frontend/src/pages/`)

| File | Description |
|------|-------------|
| `AuditPage.tsx` | Audit logs page |
| `CalendarPage.tsx` | Calendar page |
| `ChatPage.tsx` | AI Chat page |
| `DashboardPage.tsx` | Dashboard page |
| `InboxPage.tsx` | Email inbox page |
| `KnowledgeBasePage.tsx` | Knowledge base page |
| `LoginPage.tsx` | Login page |
| `MeetingsPage.tsx` | Meetings page |
| `RegisterPage.tsx` | Registration page |
| `SettingsPage.tsx` | Settings page |

### Services (`frontend/src/services/`)

| File | Description |
|------|-------------|
| `api.ts` | Axios API client configuration |
| `auditService.ts` | Audit logs API service |
| `authService.ts` | Authentication API service |
| `calendarService.ts` | Calendar API service |
| `chatService.ts` | Chat API service |
| `emailService.ts` | Email API service |
| `meetingService.ts` | Meeting API service |
| `ragService.ts` | RAG API service |
| `settingsService.ts` | Settings API service |

### State Management (`frontend/src/store/`)

| File | Description |
|------|-------------|
| `authStore.ts` | Authentication state (Zustand) |
| `settingsStore.ts` | Settings state (Zustand) |

### Tests (`frontend/src/__tests__/`)

| File | Description |
|------|-------------|
| `setup.ts` | Test setup configuration |

### Service Tests (`frontend/src/__tests__/services/`)

| File | Description |
|------|-------------|
| `api.test.ts` | API client tests |

### Store Tests (`frontend/src/__tests__/stores/`)

| File | Description |
|------|-------------|
| `authStore.test.ts` | Auth store tests |
| `settingsStore.test.ts` | Settings store tests |

### Utility Tests (`frontend/src/__tests__/utils/`)

| File | Description |
|------|-------------|
| `helpers.test.ts` | Helper function tests |

### Build Output (`frontend/dist/`)

| File | Description |
|------|-------------|
| `index.html` | Built HTML |
| `favicon.svg` | Favicon |
| `assets/index-*.css` | Built CSS |
| `assets/index-*.js` | Built JavaScript |

## Ollama (`ollama/`)

| File | Description |
|------|-------------|
| `Dockerfile` | Custom Ollama image with auto-download |
| `entrypoint.sh` | Entrypoint script that auto-downloads tinyllama |

## Documentation (`docs/`)

| File | Description |
|------|-------------|
| `CONTRIBUTING.md` | Contribution guidelines |
| `USER_GUIDE.md` | User guide |
| `performance.md` | Performance benchmarks |

## Scripts (`scripts/`)

| File | Description |
|------|-------------|
| `healthcheck.sh` | Health check script |
| `init_demo.py` | Demo data initialization script |

## Total File Count

- **Root files**: 8
- **GitHub Actions**: 2
- **Backend**: 54
- **Frontend**: 43
- **Ollama**: 2
- **Documentation**: 3
- **Scripts**: 2

**Total: 114 files**

## Docker Services

The `docker-compose.yml` configures the following services:

1. **postgres** - PostgreSQL database
2. **redis** - Redis for Celery task queue
3. **neo4j** - Neo4j graph database for RAG
4. **ollama** - Ollama LLM server (auto-downloads tinyllama)
5. **backend** - FastAPI backend
6. **worker** - Celery worker
7. **frontend** - React frontend (Nginx)

## Key Features Included

1. User authentication (JWT + 2FA TOTP)
2. Email integration (Gmail, Outlook, Yahoo, IMAP)
3. Calendar integration (Google Calendar, Outlook, Local)
4. AI Chat with LLM (Ollama tinyllama, cloud providers)
5. GraphRAG with Neo4j + LlamaIndex
6. Meeting transcription (Whisper)
7. Notifications (Slack, SMS, Email, Webhook)
8. Audit logging
9. i18n (English, Romanian)
10. Dark mode support
