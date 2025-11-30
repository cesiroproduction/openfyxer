# Contributing to OpenFyxer

Thank you for your interest in contributing to OpenFyxer! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributors of all experience levels.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git

### Development Setup

1. Fork the repository on GitHub

2. Clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/openfyxer.git
cd openfyxer
```

3. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Set up the frontend:
```bash
cd frontend
npm install
```

5. Start development services:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

6. Run the backend:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

7. Run the frontend:
```bash
cd frontend
npm run dev
```

## Development Workflow

### Branch Naming

Use descriptive branch names:
- `feature/add-calendar-sync` - New features
- `fix/email-parsing-error` - Bug fixes
- `docs/update-readme` - Documentation
- `refactor/improve-rag-service` - Code refactoring

### Commit Messages

Follow conventional commits:
- `feat: add email draft regeneration`
- `fix: resolve calendar sync timezone issue`
- `docs: update API documentation`
- `test: add unit tests for email classification`
- `refactor: simplify LLM service interface`

### Pull Requests

1. Create a feature branch from `main`
2. Make your changes
3. Write/update tests
4. Run linting and tests
5. Push to your fork
6. Open a Pull Request

## Code Style

### Python (Backend)

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use async/await for I/O operations
- Document public functions with docstrings

```python
async def classify_email(
    subject: str,
    body: str,
    sender: str,
) -> EmailCategory:
    """
    Classify an email into a category.
    
    Args:
        subject: Email subject line
        body: Email body content
        sender: Sender email address
        
    Returns:
        EmailCategory enum value
    """
    ...
```

### TypeScript (Frontend)

- Use TypeScript strict mode
- Prefer functional components with hooks
- Use named exports
- Document complex functions

```typescript
interface EmailListProps {
  emails: Email[];
  onSelect: (email: Email) => void;
  selectedId?: string;
}

export function EmailList({ emails, onSelect, selectedId }: EmailListProps) {
  // Component implementation
}
```

### CSS/Tailwind

- Use Tailwind utility classes
- Create custom components for repeated patterns
- Follow mobile-first responsive design

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_email_classification.py

# Run tests matching pattern
pytest -k "test_email"
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

### Writing Tests

- Write unit tests for business logic
- Write integration tests for API endpoints
- Mock external services
- Aim for 80%+ code coverage on new code

## Project Structure

```
openfyxer/
├── backend/
│   ├── app/
│   │   ├── api/           # API route handlers
│   │   │   └── v1/        # API version 1
│   │   ├── core/          # Core configuration
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── workers/       # Celery tasks
│   ├── tests/
│   │   ├── unit/          # Unit tests
│   │   ├── integration/   # Integration tests
│   │   └── benchmarks/    # Performance tests
│   └── alembic/           # Database migrations
├── frontend/
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API client services
│   │   ├── store/         # Zustand state stores
│   │   ├── i18n/          # Internationalization
│   │   └── __tests__/     # Frontend tests
│   └── public/            # Static assets
└── docs/                  # Documentation
```

## Adding New Features

### Adding a New API Endpoint

1. Create schema in `backend/app/schemas/`
2. Create or update model in `backend/app/models/`
3. Add service logic in `backend/app/services/`
4. Create route in `backend/app/api/v1/`
5. Register route in `backend/app/api/v1/__init__.py`
6. Write tests
7. Update API documentation

### Adding a New Frontend Page

1. Create page component in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx`
3. Create API service methods in `frontend/src/services/`
4. Add translations in `frontend/src/i18n/locales/`
5. Write tests
6. Update navigation if needed

### Adding a New Email Provider

1. Create provider class in `backend/app/services/email/providers/`
2. Implement the `EmailProvider` interface
3. Register in provider factory
4. Add OAuth routes if needed
5. Update frontend settings page
6. Write tests
7. Update documentation

### Adding a New LLM Provider

1. Create provider class in `backend/app/services/llm/providers/`
2. Implement the `LLMProvider` interface
3. Register in provider factory
4. Add configuration options
5. Update frontend settings page
6. Write tests
7. Update documentation

## Database Migrations

When modifying database models:

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Internationalization

### Adding Translations

1. Add keys to `frontend/src/i18n/locales/en.json`
2. Add translations to `frontend/src/i18n/locales/ro.json`
3. Use `useTranslation` hook in components

```typescript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  return <h1>{t('myComponent.title')}</h1>;
}
```

## Security Considerations

- Never commit secrets or credentials
- Use environment variables for configuration
- Validate all user input
- Use parameterized queries (SQLAlchemy handles this)
- Sanitize output to prevent XSS
- Follow OWASP guidelines

## Getting Help

- Open an issue for bugs or feature requests
- Join discussions for questions
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
