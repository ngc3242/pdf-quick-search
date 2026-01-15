# PDF Quick Search - Codebase Architecture Summary

## Project Overview
- Full-stack PDF document search application (Flask backend + React frontend)
- Supports PDF upload, text extraction, and full-text search
- User authentication with JWT tokens
- Multi-user document management

## Backend Structure (Flask + SQLAlchemy)

### Main Entry Point
- `/Users/heesung/coding/pdf_quick_search/backend/main.py` - Flask app initialization on port 5010
- Uses `create_app()` factory pattern in `backend/app/__init__.py`

### Database Models (SQLAlchemy)
Located in `backend/app/models/`:

1. **SearchDocument** (`document.py`)
   - Main document model with fields:
     - `id` (int, PK)
     - `owner_id` (FK to User)
     - `filename`, `original_filename`, `file_path`
     - `file_size_bytes`, `mime_type` (default: "application/pdf")
     - `page_count` (Optional)
     - `extraction_status` (pending|processing|completed|failed)
     - `extraction_error` (Optional)
     - `retry_count`, `uploaded_at`, `extraction_completed_at`
     - `is_active` (Boolean)
   - Relationships:
     - `owner` (User relationship)
     - `pages` (cascade delete SearchPage records)
     - `extraction_queue` (one-to-one ExtractionQueue)
   - Method: `to_dict()` for serialization

2. **SearchPage** (`page.py`)
   - Stores extracted text per PDF page:
     - `id` (int, PK)
     - `document_id` (FK to SearchDocument)
     - `page_number` (int)
     - `content` (Text - full extracted text)
     - `content_normalized` (Text - lowercase, normalized for searching)
     - Unique constraint on (document_id, page_number)
   - Relationship: `document` (back_populates SearchDocument.pages)

3. **ExtractionQueue** (`extraction_queue.py`)
   - Manages PDF text extraction jobs:
     - `id` (int, PK)
     - `document_id` (FK to SearchDocument)
     - `priority` (int, default 0)
     - `status` (pending|processing|completed|failed)
     - `created_at`, `started_at`, `completed_at` (timestamps)
     - `error_message`, `retry_count`

4. **User** (`user.py`) - Basic user model with email/password auth

5. **TokenBlacklist** (`token_blacklist.py`) - JWT token revocation

### Services (Business Logic)
Located in `backend/app/services/`:

1. **DocumentService** (`document_service.py`)
   - `upload_document(file, owner_id)` - uploads PDF and adds to extraction queue
   - `get_documents_by_owner(owner_id, page, per_page)` - paginated listing
   - `get_document_by_id(document_id)` - single document retrieval
   - `delete_document(document_id, owner_id)` - soft/hard delete with file cleanup
   - `verify_document_access(document_id, owner_id)` - ownership verification

2. **SearchService** (`search_service.py`)
   - Constants: MIN_QUERY_LENGTH=2, DEFAULT_LIMIT=50, MAX_LIMIT=100
   - `search(user_id, query, limit, offset)` - full-text search using ILIKE on content_normalized
   - Returns: (list[SearchResult], total_count)
   - `generate_snippet(content, query, context_length)` - creates context-aware text snippets
   - Joins SearchPage with SearchDocument, filters by extraction_status="completed"

3. **ExtractionService** (`extraction_service.py`)
   - `normalize_text(text)` - Unicode NFC normalization, lowercase, whitespace normalization
   - `add_to_queue(document_id, priority)` - queues documents for processing
   - `get_next_pending()` - retrieves next job by priority then FIFO
   - `extract_text(document_id)` - uses pdfplumber to extract text from PDF pages
   - MAX_RETRIES = 3

4. **AuthService**, **AdminService** - User authentication and admin operations

### API Routes (Flask Blueprints)
Located in `backend/app/routes/`:

1. **documents.py** - `/api/documents`
   - POST - Upload document (multipart/form-data) → 202 Accepted
   - GET - List documents (pagination) → DocumentsResponse
   - GET /{id} - Get document details
   - DELETE /{id} - Delete document
   - GET /{id}/file - Download PDF (supports Range header for partial content)

2. **search.py** - `/api/search`
   - GET - Search documents
   - Params: q (required), limit (default 50), offset (default 0)
   - Returns: SearchResponse with results array and total count

3. **auth.py**, **health.py**, **admin.py** - Authentication and management endpoints

### Configuration
- `backend/config.py`:
  - Base Config, DevelopmentConfig, TestingConfig, ProductionConfig
  - Database: PostgreSQL (dev: localhost:5432/pdf_search_dev)
  - JWT: 24-hour token expiry
  - File Storage: `storage/uploads` directory
  - MAX_CONTENT_LENGTH: 50MB
  - ALLOWED_EXTENSIONS: {pdf}

### Testing
- `backend/tests/conftest.py` - Pytest fixtures
  - `app` fixture - fresh test app with in-memory SQLite
  - `client` fixture - Flask test client
  - `db_session` fixture - database session
- Test files: test_documents.py, test_search.py, test_auth.py, test_models.py, test_extraction_service.py, etc.
- Uses pytest with coverage tracking

### Background Processing
- `backend/app/worker.py` - Extraction worker (adaptive polling with APScheduler)
- Processes ExtractionQueue items asynchronously
- Updates SearchDocument.extraction_status and creates SearchPage records

### Utilities
- `backend/app/utils/auth.py` - JWT authentication decorator (@jwt_required)
- `backend/app/utils/storage.py` - File operations (allowed_file, save_file, delete_file)

## Frontend Structure (React + TypeScript)

### Tech Stack
- React 19.2.0 with TypeScript 5.9
- Vite build tool
- Zustand for state management
- Tailwind CSS for styling
- Axios for HTTP client
- React Router v7 for navigation
- React PDF for PDF viewer

### Directory Structure
- `frontend/src/pages/` - Page components
  - LoginPage.tsx
  - DocumentsPage.tsx
  - SearchPage.tsx
  - AdminPage.tsx

- `frontend/src/components/` - UI components
  - `search/` - Search components
  - `documents/` - Document list/upload components
  - `viewer/` - PDF viewer components
  - `auth/` - Auth components
  - `admin/` - Admin management components
  - `common/` - Shared UI components

- `frontend/src/api/` - API client layer
  - `client.ts` - Axios instance with auth interceptor
  - `documentApi.ts` - Document operations (list, get, upload, delete, getFileUrl)
  - `searchApi.ts` - Search operations
  - `authApi.ts`, `adminApi.ts` - Auth and admin APIs

- `frontend/src/store/` - Zustand state management
- `frontend/src/types/index.ts` - TypeScript interfaces

### Data Types (TypeScript)
```
User: { id, email, name, phone, role, is_active, created_at }
Document: { id, owner_id, filename, original_filename, file_size_bytes, mime_type, 
            page_count, extraction_status, extraction_error, uploaded_at, 
            extraction_completed_at, is_active }
DocumentsResponse: { documents[], total, page, per_page, pages }
SearchResult: { document, page_number, snippet }
SearchResponse: { results[], total, query, limit, offset }
```

## Key Patterns for CrossRef DOI Integration

### Document Enhancement Point
- SearchDocument model is the ideal place to add DOI metadata
- Consider adding optional fields: `doi`, `doi_lookup_status`, `doi_metadata`

### Service Layer Pattern
- Create new service: `backend/app/services/doi_service.py`
- Implement DOI lookup, validation, and metadata caching
- Similar pattern to ExtractionService for async processing

### API Integration Pattern
- Add new endpoint: `/api/documents/{id}/doi` for DOI lookup
- Or extend SearchDocument response to include DOI metadata
- Follow existing 202 Accepted pattern for async operations

### Queue Processing Pattern
- Extend ExtractionQueue or create DuplicateDetectionQueue
- Process DOI lookups and duplicate detection during extraction
- Update SearchDocument metadata after successful lookup

### Frontend Integration Points
- DocumentsPage.tsx - Display DOI information
- SearchPage.tsx - Show DOI in search results
- Consider adding DOI search filter capability

### Testing Patterns
- Follow conftest.py fixture pattern
- Use pytest with mocked API responses
- Test both successful and failed DOI lookups

## Important Notes for Implementation
- All services use dependency injection via imports
- Database uses SQLAlchemy ORM with Alembic migrations
- PDF extraction uses pdfplumber library (already in requirements)
- File storage is local filesystem (configurable via UPLOAD_FOLDER)
- Authentication is JWT-based with token in Authorization header
- All user data is scoped by owner_id for multi-tenant support
