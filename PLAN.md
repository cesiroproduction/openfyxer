# OpenFyxer - Project Plan

## Executive Summary

OpenFyxer is an open-source, self-hosted AI executive assistant similar to and superior to Fyxer.ai. It provides intelligent email management, calendar assistance, meeting transcription, and a powerful GraphRAG knowledge base - all running locally with optional cloud LLM support.

## Project Vision

**Core Principles:**
- **Data Sovereignty**: All data stays on user's infrastructure
- **Offline-First**: Full functionality without internet (except email/calendar APIs)
- **Single-User, Multi-Account**: One user with multiple email accounts
- **Bilingual**: Full RO/EN support for UI and AI responses

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy + Alembic migrations
- **Validation**: Pydantic v2
- **Task Queue**: Celery + Redis
- **Authentication**: OAuth2 + JWT + TOTP 2FA

### Frontend
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: React Query + Zustand
- **i18n**: react-i18next (RO/EN)
- **Build**: Vite

### Databases
- **Relational**: PostgreSQL 16 (production) / SQLite (fallback)
- **Graph**: Neo4j Community Edition 5.x
- **Cache**: Redis 7.x

### AI/ML
- **LLM Local**: llama-cpp-python with GGUF models
- **LLM Cloud**: OpenAI, Gemini, Claude, Cohere (optional)
- **RAG**: LlamaIndex + Neo4j PropertyGraphIndex
- **Embeddings**: Local (sentence-transformers) or OpenAI
- **STT**: Faster-Whisper (offline transcription)

### Infrastructure
- **Containers**: Docker + docker-compose
- **CI/CD**: GitHub Actions
- **LLM Server**: Ollama (optional GPU acceleration)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Frontend │  │ Backend  │  │ Postgres │  │  Neo4j   │        │
│  │  (React) │  │ (FastAPI)│  │    DB    │  │  Graph   │        │
│  │  :3000   │  │  :8000   │  │  :5432   │  │  :7687   │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │             │             │               │
│       └─────────────┼─────────────┼─────────────┘               │
│                     │             │                             │
│  ┌──────────┐  ┌────┴─────┐  ┌───┴──────┐                      │
│  │  Redis   │  │  Ollama  │  │  Worker  │                      │
│  │  Cache   │  │   LLM    │  │ (Celery) │                      │
│  │  :6379   │  │  :11434  │  │          │                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

## Feature Modules

### 1. Inbox Assistant
- Auto-triage emails: Urgent / To Respond / FYI / Newsletter / Spam
- Generate draft responses in user's style (RO/EN)
- Configurable follow-up reminders
- Newsletter unsubscribe management
- Auto-organize into folders/labels
- Intelligent RAG-powered search

### 2. Calendar Assistant
- Sync with Google Calendar / Outlook Calendar
- Auto-propose meeting slots (time blocking, priority hours, buffer)
- Conflict detection and rescheduling proposals
- Meeting reminders

### 3. Meeting Intelligence
- Audio upload/recording for meetings
- Offline transcription (Faster-Whisper)
- Meeting summarization (executive summary + action items)
- Auto-generate follow-up emails

### 4. GraphRAG Knowledge Base
- Ingest all emails + attachments + documents
- Build knowledge graph in Neo4j (Person, Company, Project, Email, Document, Meeting, Topic)
- Store embeddings in Neo4j vector store
- Semantic Q&A through LlamaIndex

### 5. Web Interface (React)
- Dashboard: time saved, process status, pending actions
- Inbox: categorized emails, Accept/Edit/Send for drafts
- Calendar: unified view, scheduling
- Knowledge Base: indexed documents, manual upload
- Settings: email accounts, API keys, LLM config, notifications, style preferences
- Audit Logs: AI actions history
- AI Chat: conversational interface over knowledge base

### 6. Notifications
- Slack (webhook/bot)
- SMS (Twilio or configurable)
- Email notifications
- Generic webhook

## Security Requirements

- Username + password authentication (bcrypt/argon2)
- Optional 2FA TOTP (Google Authenticator compatible)
- OAuth2 tokens encrypted in database (pgcrypto)
- Audit trail for all actions
- XSS/CSRF protection
- No sensitive data to cloud LLM without explicit consent
- All secrets via environment variables

## Development Phases

### Phase 1: Foundation (Week 1)
- [x] Project structure setup
- [ ] Docker infrastructure (docker-compose.yml)
- [ ] Backend skeleton (FastAPI + SQLAlchemy)
- [ ] Database models and migrations
- [ ] Authentication system (JWT + 2FA)

### Phase 2: Core Integrations (Week 2-3)
- [ ] Email integration (Gmail OAuth2, Outlook, Yahoo, IMAP)
- [ ] Calendar integration (Google Calendar, Outlook)
- [ ] Email sync and storage

### Phase 3: AI Engine (Week 3-4)
- [ ] LLM module (local GGUF + cloud providers)
- [ ] GraphRAG setup (Neo4j + LlamaIndex)
- [ ] Email classification
- [ ] Draft generation with style learning

### Phase 4: Advanced Features (Week 4-5)
- [ ] STT module (Faster-Whisper)
- [ ] Meeting transcription and summarization
- [ ] Notifications module
- [ ] Follow-up automation

### Phase 5: Frontend (Week 5-7)
- [ ] React app setup with TypeScript
- [ ] Authentication UI
- [ ] Dashboard page
- [ ] Inbox page with draft management
- [ ] Calendar page
- [ ] Knowledge Base page
- [ ] Settings page
- [ ] Audit logs page
- [ ] AI Chat interface
- [ ] i18n (RO/EN)

### Phase 6: Testing & Polish (Week 7-8)
- [ ] Unit tests (pytest)
- [ ] Integration tests
- [ ] Performance benchmarks
- [ ] Security audit
- [ ] Documentation

### Phase 7: Release (Week 8)
- [ ] Final docker-compose validation
- [ ] Demo scripts
- [ ] CI/CD pipeline
- [ ] Release v1.0

## Deliverables

1. **Repository** with:
   - Backend FastAPI code
   - Frontend React code
   - Email/Calendar integration modules
   - RAG/GraphRAG module (LlamaIndex + Neo4j)
   - LLM module (local + cloud)
   - Notifications module
   - STT module
   - Tests (unit + integration)
   - Demo population scripts

2. **docker-compose.yml** starting:
   - Backend service
   - Frontend service
   - PostgreSQL
   - Neo4j
   - Redis
   - Ollama (LLM server)

3. **Documentation**:
   - README with installation steps
   - Architecture diagrams
   - User guide with screenshots
   - Contributor guide

4. **CI/CD**:
   - GitHub Actions (lint + test + build Docker images)

5. **Benchmarks**:
   - Email processing time
   - RAG query response time
   - Results in docs/performance.md

## Hardware Requirements

- **Minimum**: 4-core CPU, 16GB RAM (7B parameter models, quantized)
- **Recommended**: Apple Silicon M1+ or NVIDIA GPU 8GB+ VRAM
- **Storage**: 50GB SSD (Docker images + Neo4j data)

## Team Roles (Simulated)

- **Architect**: System design, docker-compose, module interfaces
- **Backend Dev**: FastAPI, integrations, business logic
- **AI/RAG Engineer**: LlamaIndex, Neo4j, LLM integration
- **Frontend Dev**: React dashboard, UI/UX
- **DevOps**: Docker, CI/CD, deployment
- **QA**: Testing, benchmarks
- **Security**: Auth, encryption, audit
- **Docs**: README, guides, API documentation

## Success Criteria

1. `docker-compose up` starts entire stack
2. User can login with 2FA
3. Connect at least one email account
4. Emails are fetched and categorized
5. AI generates draft responses
6. Documents indexed in Neo4j
7. RAG queries return accurate answers
8. UI fully functional in RO and EN
9. All tests pass
10. Documentation complete for self-installation
