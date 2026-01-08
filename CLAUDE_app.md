# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Quick Search is a PDF document management and search service with user isolation. Users can upload PDF documents, which are processed for text extraction, and then search across their documents.

## Development Commands

### Backend (Flask)

```bash
cd backend
source venv/bin/activate

# Run development server (port 5010)
python main.py

# Run all tests with coverage
pytest --cov=app --cov-report=html

# Run a single test file
pytest tests/test_auth.py

# Run a specific test
pytest tests/test_auth.py::test_login_success -v

# Database migrations
flask db upgrade    # Apply migrations
flask db migrate    # Generate migration after model changes
```

### Frontend (React + Vite)

```bash
cd frontend

# Development server (port 3000, proxies /api to backend)
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

## Architecture

### Backend Structure

The backend uses Flask with the application factory pattern (`app/__init__.py`).

- **Routes** (`app/routes/`): API endpoints organized by feature
  - `auth.py`: Login/logout, JWT authentication
  - `documents.py`: PDF upload, list, download with Range support
  - `search.py`: Full-text search across user's documents
  - `admin.py`: User management (admin only)

- **Services** (`app/services/`): Business logic layer
  - `auth_service.py`: Authentication logic
  - `document_service.py`: Document CRUD operations
  - `extraction_service.py`: PDF text extraction using pdfplumber
  - `search_service.py`: Search implementation

- **Models** (`app/models/`): SQLAlchemy models
  - `User`: With roles (admin/user) and bcrypt password hashing
  - `Document`: PDF metadata, linked to owner
  - `Page`: Extracted text content per page
  - `ExtractionQueue`: Background processing queue
  - `TokenBlacklist`: Invalidated JWT tokens

- **Utils** (`app/utils/`):
  - `auth.py`: JWT token handling, `@jwt_required` decorator
  - `storage.py`: File system operations for PDFs
  - `admin.py`: Admin role check decorator

### Frontend Structure

React 19 with TypeScript, using Vite for bundling.

- **State Management**: Zustand stores in `src/store/`
  - `authStore.ts`: User auth state with persistence
  - `documentStore.ts`: Document list and operations

- **API Layer** (`src/api/`):
  - `client.ts`: Axios instance with JWT interceptor (auto-adds Bearer token, redirects to /login on 401)
  - Feature-specific API modules

- **Pages** (`src/pages/`):
  - `LoginPage`: Authentication
  - `SearchPage`: Main search interface (default route)
  - `DocumentsPage`: Document upload and management
  - `AdminPage`: User administration (requires admin role)

- **Components** (`src/components/`): Organized by feature (auth, documents, search, admin, common)

- **Routing**: React Router with `ProtectedRoute` wrapper that checks auth and optionally requires admin role

### Key Integration Points

- Frontend proxies `/api/*` to `localhost:5010` (configured in `vite.config.ts`)
- JWT tokens stored in localStorage as `access_token`
- Path alias `@/` maps to `src/` directory

## Testing

Backend tests are in `backend/tests/`. Tests use an in-memory SQLite database and fresh fixtures per test function (see `conftest.py`).

Key test fixtures:
- `app`: Fresh Flask app with clean database
- `client`: Test client for HTTP requests
- `db_session`: Database session

## Configuration

Backend configuration uses environment variables (`.env`) with fallbacks in `config.py`:
- `development`: Debug mode, PostgreSQL
- `testing`: SQLite in-memory, test upload folder
- `production`: Debug disabled

Required databases: `pdf_search_dev`, `pdf_search_test` (PostgreSQL)
