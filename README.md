# OpenFyxer - AI Executive Assistant

OpenFyxer is an open-source, self-hosted AI executive assistant similar to Fyxer.ai. It provides intelligent email management, calendar integration, meeting intelligence, and a knowledge base powered by GraphRAG.

## Features

**Inbox Assistant**
- Automatic email triage into categories (Urgent, To Respond, FYI, Newsletter, Spam)
- AI-generated draft responses in your writing style
- Support for Romanian and English languages
- Configurable follow-up reminders
- Smart search using RAG (find emails by content, not just keywords)

**Calendar Assistant**
- Sync with Google Calendar and Outlook
- Automatic meeting slot suggestions
- Conflict detection and resolution
- Buffer time management between meetings

**Meeting Intelligence**
- Audio upload and transcription (Whisper-based STT)
- AI-powered meeting summarization
- Action item extraction
- Automatic follow-up email generation

**Knowledge Base (GraphRAG)**
- Index all emails, documents, and meeting notes
- Neo4j-powered knowledge graph
- Semantic search with vector embeddings
- Context-aware Q&A

**Multi-Provider Support**
- Email: Gmail, Outlook, Yahoo, Generic IMAP
- LLM: Local (Ollama), OpenAI, Google Gemini, Anthropic Claude, Cohere
- Calendar: Google Calendar, Outlook Calendar

## Requirements

**Hardware**
- CPU: 4+ cores recommended
- RAM: 8GB minimum, 16GB recommended for local LLM
- Storage: 20GB+ for models and data

**Software**
- Docker and Docker Compose
- Git

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/horecacesiro/openfyxer.git
cd openfyxer
```

2. Copy the example environment file:
```bash
cp .env.example .env
```

3. Edit `.env` with your configuration (see Configuration section)

4. Start the stack:
```bash
docker-compose up -d
```

5. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

6. Create your account and start configuring email accounts

## Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Application
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=false

# Database
DATABASE_URL=postgresql://openfyxer:openfyxer@postgres:5432/openfyxer

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Redis
REDIS_URL=redis://redis:6379/0

# Email Providers (Optional - configure in UI)
GMAIL_CLIENT_ID=your-gmail-client-id
GMAIL_CLIENT_SECRET=your-gmail-client-secret
OUTLOOK_CLIENT_ID=your-outlook-client-id
OUTLOOK_CLIENT_SECRET=your-outlook-client-secret

# LLM Providers (Optional - configure in UI)
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
COHERE_API_KEY=your-cohere-api-key

# Local LLM (Ollama)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama2

# Notifications (Optional)
SLACK_WEBHOOK_URL=your-slack-webhook-url
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_FROM_NUMBER=your-twilio-phone-number
```

### Email Provider Setup

**Gmail**
1. Go to Google Cloud Console
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8000/api/v1/email/oauth/gmail/callback`
6. Copy Client ID and Client Secret to `.env`

**Outlook**
1. Go to Azure Portal
2. Register a new application
3. Add Microsoft Graph permissions (Mail.Read, Mail.Send, Calendars.ReadWrite)
4. Create a client secret
5. Add redirect URI: `http://localhost:8000/api/v1/email/oauth/outlook/callback`
6. Copy Application ID and Client Secret to `.env`

**Yahoo / Generic IMAP**
- Configure directly in the UI with IMAP/SMTP credentials
- For Yahoo, generate an app-specific password

### LLM Configuration

**Local LLM (Default)**
- Uses Ollama with llama2 model by default
- No API keys required
- Runs entirely offline

**Cloud LLM Providers**
- Configure API keys in `.env` or through the Settings page
- Select preferred provider in Settings > LLM Settings

## Architecture

```
openfyxer/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # API endpoints
│   │   ├── core/      # Core configuration
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   └── workers/   # Celery tasks
│   └── tests/         # Backend tests
├── frontend/          # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API services
│   │   ├── store/       # Zustand stores
│   │   └── i18n/        # Translations
│   └── tests/           # Frontend tests
├── docker-compose.yml   # Docker orchestration
└── docs/                # Documentation
```

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

**Backend Tests**
```bash
cd backend
pytest
```

**Frontend Tests**
```bash
cd frontend
npm test
```

## Security

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- Optional TOTP-based 2FA
- OAuth tokens encrypted at rest
- Audit logging for all actions
- CSRF protection
- Input validation and sanitization

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Updating

OpenFyxer does not auto-update. To update:

```bash
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

## Troubleshooting

**Container won't start**
- Check logs: `docker-compose logs -f`
- Ensure ports 3000, 8000, 5432, 7474, 7687, 6379 are available

**Email sync not working**
- Verify OAuth credentials are correct
- Check if tokens have expired (re-authenticate)
- Review backend logs for specific errors

**LLM responses slow**
- Local LLM requires significant CPU/RAM
- Consider using cloud LLM for faster responses
- Reduce model size in Ollama settings

**Neo4j connection issues**
- Wait for Neo4j to fully initialize (can take 1-2 minutes)
- Check Neo4j logs: `docker-compose logs neo4j`

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://react.dev/) - Frontend framework
- [Neo4j](https://neo4j.com/) - Graph database
- [LlamaIndex](https://www.llamaindex.ai/) - RAG framework
- [Ollama](https://ollama.ai/) - Local LLM runtime
- [Whisper](https://github.com/openai/whisper) - Speech-to-text
# openfyxer
