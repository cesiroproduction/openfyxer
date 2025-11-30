# OpenFyxer - Architecture Documentation

## System Overview

OpenFyxer is a containerized, self-hosted AI executive assistant built on a microservices architecture. The system is designed for offline-first operation with optional cloud LLM integration.

## Container Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Docker Compose Stack                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│  │    frontend     │     │     backend     │     │     worker      │       │
│  │   (React/Vite)  │────▶│    (FastAPI)    │◀────│    (Celery)     │       │
│  │    Port 3000    │     │    Port 8000    │     │                 │       │
│  └─────────────────┘     └────────┬────────┘     └────────┬────────┘       │
│                                   │                       │                 │
│           ┌───────────────────────┼───────────────────────┤                 │
│           │                       │                       │                 │
│           ▼                       ▼                       ▼                 │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│  │    postgres     │     │      neo4j      │     │      redis      │       │
│  │  (PostgreSQL)   │     │  (Graph + Vec)  │     │     (Cache)     │       │
│  │    Port 5432    │     │  Ports 7474/87  │     │    Port 6379    │       │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘       │
│                                                                              │
│  ┌─────────────────┐                                                        │
│  │     ollama      │                                                        │
│  │   (LLM Server)  │                                                        │
│  │   Port 11434    │                                                        │
│  └─────────────────┘                                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Service Descriptions

### 1. Frontend Service (frontend)
- **Technology**: React 18 + TypeScript + Vite
- **Port**: 3000
- **Purpose**: Web dashboard for user interaction
- **Features**:
  - PWA-capable for mobile access
  - Offline caching with Service Workers
  - Real-time updates via WebSocket
  - i18n support (RO/EN)

### 2. Backend Service (backend)
- **Technology**: Python 3.11 + FastAPI
- **Port**: 8000
- **Purpose**: API Gateway, business logic, orchestration
- **Responsibilities**:
  - Authentication (JWT + 2FA)
  - API endpoints for all features
  - Email/Calendar sync coordination
  - LLM request routing
  - WebSocket connections

### 3. Worker Service (worker)
- **Technology**: Celery + Redis
- **Purpose**: Async task processing
- **Tasks**:
  - Email fetching and processing
  - Document indexing
  - Draft generation
  - Meeting transcription
  - Notification dispatch

### 4. PostgreSQL (postgres)
- **Version**: 16
- **Port**: 5432
- **Purpose**: Relational data storage
- **Stores**:
  - User accounts and preferences
  - Email metadata
  - Calendar events
  - OAuth tokens (encrypted)
  - Audit logs
  - Draft responses

### 5. Neo4j (neo4j)
- **Version**: Community 5.x
- **Ports**: 7474 (HTTP), 7687 (Bolt)
- **Purpose**: Knowledge graph + vector store
- **Features**:
  - APOC plugin for advanced operations
  - Vector index for embeddings
  - Property graph for relationships

### 6. Redis (redis)
- **Version**: 7.x
- **Port**: 6379
- **Purpose**: Cache and message broker
- **Uses**:
  - Celery task queue
  - Session cache
  - Rate limiting
  - Real-time pub/sub

### 7. Ollama (ollama)
- **Port**: 11434
- **Purpose**: Local LLM inference server
- **Features**:
  - OpenAI-compatible API
  - GPU acceleration (optional)
  - Multiple model support

## Backend Module Architecture

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry
│   ├── api/
│   │   └── v1/
│   │       ├── router.py       # API router aggregation
│   │       └── endpoints/
│   │           ├── auth.py     # Authentication endpoints
│   │           ├── users.py    # User management
│   │           ├── emails.py   # Email operations
│   │           ├── calendar.py # Calendar operations
│   │           ├── drafts.py   # Draft management
│   │           ├── rag.py      # RAG queries
│   │           ├── meetings.py # Meeting transcription
│   │           ├── settings.py # User settings
│   │           └── chat.py     # AI chat interface
│   ├── core/
│   │   ├── config.py           # Settings and env vars
│   │   ├── security.py         # Auth utilities
│   │   ├── encryption.py       # Token encryption
│   │   └── exceptions.py       # Custom exceptions
│   ├── db/
│   │   ├── session.py          # Database session
│   │   ├── base.py             # SQLAlchemy base
│   │   └── init_db.py          # DB initialization
│   ├── models/
│   │   ├── user.py             # User model
│   │   ├── email_account.py    # Email account model
│   │   ├── email.py            # Email model
│   │   ├── calendar_event.py   # Calendar event model
│   │   ├── draft.py            # Draft model
│   │   ├── document.py         # Document model
│   │   ├── meeting.py          # Meeting model
│   │   └── audit_log.py        # Audit log model
│   ├── schemas/
│   │   ├── user.py             # User schemas
│   │   ├── email.py            # Email schemas
│   │   ├── calendar.py         # Calendar schemas
│   │   ├── draft.py            # Draft schemas
│   │   ├── rag.py              # RAG schemas
│   │   └── settings.py         # Settings schemas
│   ├── services/
│   │   ├── email/
│   │   │   ├── gmail.py        # Gmail integration
│   │   │   ├── outlook.py      # Outlook integration
│   │   │   ├── imap.py         # Generic IMAP
│   │   │   └── classifier.py   # Email classification
│   │   ├── calendar/
│   │   │   ├── google.py       # Google Calendar
│   │   │   ├── outlook.py      # Outlook Calendar
│   │   │   └── scheduler.py    # Meeting scheduler
│   │   ├── llm/
│   │   │   ├── local.py        # Local LLM (Ollama)
│   │   │   ├── openai.py       # OpenAI integration
│   │   │   ├── gemini.py       # Gemini integration
│   │   │   ├── claude.py       # Claude integration
│   │   │   ├── cohere.py       # Cohere integration
│   │   │   └── router.py       # LLM routing logic
│   │   ├── rag/
│   │   │   ├── indexer.py      # Document indexing
│   │   │   ├── graph.py        # Neo4j graph operations
│   │   │   ├── embeddings.py   # Embedding generation
│   │   │   └── query.py        # RAG query engine
│   │   ├── stt/
│   │   │   └── whisper.py      # Whisper transcription
│   │   └── notifications/
│   │       ├── slack.py        # Slack notifications
│   │       ├── sms.py          # SMS notifications
│   │       ├── email.py        # Email notifications
│   │       └── webhook.py      # Webhook notifications
│   ├── utils/
│   │   ├── language.py         # Language detection
│   │   └── style.py            # Style analysis
│   └── workers/
│       ├── email_tasks.py      # Email processing tasks
│       ├── rag_tasks.py        # RAG indexing tasks
│       ├── meeting_tasks.py    # Meeting processing tasks
│       └── notification_tasks.py # Notification tasks
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── unit/
│   └── integration/
├── pyproject.toml
└── Dockerfile
```

## Database Schema

### PostgreSQL Tables

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    totp_secret VARCHAR(255),  -- Encrypted
    is_active BOOLEAN DEFAULT true,
    language VARCHAR(5) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Email accounts
CREATE TABLE email_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    provider VARCHAR(50) NOT NULL,  -- gmail, outlook, yahoo, imap
    email_address VARCHAR(255) NOT NULL,
    oauth_token TEXT,  -- Encrypted
    oauth_refresh_token TEXT,  -- Encrypted
    imap_password TEXT,  -- Encrypted (for non-OAuth)
    last_sync TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Emails
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES email_accounts(id),
    message_id VARCHAR(255) NOT NULL,
    thread_id VARCHAR(255),
    subject TEXT,
    sender VARCHAR(255),
    recipients TEXT[],
    body_text TEXT,
    body_html TEXT,
    category VARCHAR(50),  -- urgent, to_respond, fyi, newsletter, spam
    has_attachments BOOLEAN DEFAULT false,
    is_read BOOLEAN DEFAULT false,
    received_at TIMESTAMP,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(account_id, message_id)
);

-- Drafts
CREATE TABLE drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID REFERENCES emails(id),
    user_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, approved, sent, rejected
    llm_model VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP
);

-- Calendar events
CREATE TABLE calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    provider VARCHAR(50) NOT NULL,
    external_id VARCHAR(255),
    title VARCHAR(500),
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    location VARCHAR(500),
    attendees TEXT[],
    is_all_day BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    email_id UUID REFERENCES emails(id),  -- NULL if manually uploaded
    filename VARCHAR(255),
    file_type VARCHAR(50),
    file_size INTEGER,
    content_text TEXT,
    indexed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Meetings
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    calendar_event_id UUID REFERENCES calendar_events(id),
    audio_file_path VARCHAR(500),
    transcript TEXT,
    summary TEXT,
    action_items TEXT[],
    transcribed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT NOW()
);

-- User settings
CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) UNIQUE,
    llm_provider VARCHAR(50) DEFAULT 'local',
    llm_model VARCHAR(100),
    openai_api_key TEXT,  -- Encrypted
    gemini_api_key TEXT,  -- Encrypted
    claude_api_key TEXT,  -- Encrypted
    cohere_api_key TEXT,  -- Encrypted
    slack_webhook_url TEXT,
    sms_provider VARCHAR(50),
    sms_api_key TEXT,  -- Encrypted
    sms_phone_number VARCHAR(20),
    notification_email VARCHAR(255),
    email_style TEXT,  -- Learned style preferences
    follow_up_days INTEGER DEFAULT 3,
    priority_contacts TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Neo4j Graph Schema

```cypher
// Node types
(:Person {id, name, email, company, role})
(:Company {id, name, domain})
(:Email {id, subject, date, category})
(:Document {id, filename, type, content_embedding})
(:Meeting {id, title, date, summary})
(:Project {id, name, description})
(:Topic {id, name})

// Relationships
(:Person)-[:SENT]->(:Email)
(:Person)-[:RECEIVED]->(:Email)
(:Person)-[:WORKS_AT]->(:Company)
(:Person)-[:ATTENDED]->(:Meeting)
(:Email)-[:HAS_ATTACHMENT]->(:Document)
(:Email)-[:MENTIONS]->(:Person)
(:Email)-[:MENTIONS]->(:Company)
(:Email)-[:MENTIONS]->(:Project)
(:Email)-[:ABOUT]->(:Topic)
(:Meeting)-[:DISCUSSED]->(:Topic)
(:Meeting)-[:RELATED_TO]->(:Project)
(:Document)-[:RELATED_TO]->(:Project)

// Vector index for semantic search
CREATE VECTOR INDEX email_embeddings FOR (e:Email) ON e.embedding
OPTIONS {indexConfig: {`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}}
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (returns JWT)
- `POST /api/v1/auth/2fa/setup` - Setup 2FA
- `POST /api/v1/auth/2fa/verify` - Verify 2FA code
- `POST /api/v1/auth/refresh` - Refresh JWT token
- `POST /api/v1/auth/logout` - Logout

### Email Accounts
- `GET /api/v1/accounts` - List email accounts
- `POST /api/v1/accounts` - Add email account
- `DELETE /api/v1/accounts/{id}` - Remove account
- `POST /api/v1/accounts/{id}/sync` - Trigger sync

### Emails
- `GET /api/v1/emails` - List emails (with filters)
- `GET /api/v1/emails/{id}` - Get email details
- `PATCH /api/v1/emails/{id}` - Update email (category, read status)
- `POST /api/v1/emails/{id}/draft` - Generate draft response

### Drafts
- `GET /api/v1/drafts` - List pending drafts
- `GET /api/v1/drafts/{id}` - Get draft
- `PATCH /api/v1/drafts/{id}` - Edit draft
- `POST /api/v1/drafts/{id}/send` - Send draft
- `DELETE /api/v1/drafts/{id}` - Reject draft

### Calendar
- `GET /api/v1/calendar/events` - List events
- `POST /api/v1/calendar/events` - Create event
- `GET /api/v1/calendar/slots` - Get available slots
- `POST /api/v1/calendar/schedule` - Auto-schedule meeting

### RAG / Knowledge Base
- `POST /api/v1/rag/query` - Query knowledge base
- `GET /api/v1/rag/documents` - List indexed documents
- `POST /api/v1/rag/documents` - Upload document
- `DELETE /api/v1/rag/documents/{id}` - Remove document

### Meetings
- `POST /api/v1/meetings/upload` - Upload audio
- `GET /api/v1/meetings/{id}` - Get meeting details
- `POST /api/v1/meetings/{id}/transcribe` - Trigger transcription
- `POST /api/v1/meetings/{id}/summarize` - Generate summary

### Settings
- `GET /api/v1/settings` - Get user settings
- `PATCH /api/v1/settings` - Update settings
- `POST /api/v1/settings/test-notification` - Test notification

### Chat
- `POST /api/v1/chat` - Send message to AI
- `GET /api/v1/chat/history` - Get chat history

### Audit
- `GET /api/v1/audit` - Get audit logs

## Security Architecture

### Authentication Flow
```
1. User submits credentials
2. Backend validates password (bcrypt)
3. If 2FA enabled, prompt for TOTP code
4. Generate JWT access token (15min) + refresh token (7d)
5. Store refresh token hash in DB
6. Return tokens to client
```

### Token Encryption
- OAuth tokens encrypted with AES-256-GCM
- Master key derived from environment variable
- Key rotation supported

### API Security
- Rate limiting (100 req/min per user)
- CORS configured for frontend origin only
- CSRF tokens for state-changing operations
- Input validation with Pydantic
- SQL injection prevention via ORM
- XSS prevention in responses

## Data Flow

### Email Processing Pipeline
```
1. Celery worker fetches new emails via API/IMAP
2. Email stored in PostgreSQL
3. Classification via LLM (category assignment)
4. Entity extraction for Neo4j graph
5. Embedding generation for vector search
6. If "to_respond", generate draft via LLM
7. Notify user if urgent
```

### RAG Query Pipeline
```
1. User submits natural language query
2. Generate query embedding
3. Vector search in Neo4j for relevant nodes
4. Graph traversal for related entities
5. Combine context from vector + graph results
6. Send to LLM with context
7. Return answer with source citations
```

## Performance Considerations

### Caching Strategy
- Redis cache for:
  - User sessions
  - Recent email lists
  - LLM responses (with TTL)
  - Rate limit counters

### Async Processing
- All email sync operations are async (Celery)
- Document indexing runs in background
- Draft generation is async with WebSocket notification

### Database Optimization
- PostgreSQL indexes on frequently queried columns
- Neo4j indexes on node properties
- Connection pooling for both databases

## Monitoring

### Health Checks
- `/health` - Overall system health
- `/health/db` - Database connectivity
- `/health/neo4j` - Neo4j connectivity
- `/health/redis` - Redis connectivity
- `/health/llm` - LLM server status

### Metrics
- Request latency
- Email processing time
- RAG query response time
- LLM inference time
- Queue depth

## Deployment

### Development
```bash
docker-compose -f docker-compose.dev.yml up
```

### Production
```bash
docker-compose up -d
```

### Environment Variables
See `.env.example` for all required configuration.
