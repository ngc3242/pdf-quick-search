# PDF Quick Search

PDF document management and search service with user isolation.

## Features

- User authentication with JWT tokens
- PDF document upload and management
- User-based document isolation
- Full-text search with PDF text extraction
- Document download with Range support
- Modern React UI with SARA-style design
- Admin user management
- CrossRef DOI metadata integration (SPEC-CROSSREF-001)
  - Automatic DOI extraction from PDF documents
  - CrossRef API integration with caching (7-day TTL)
  - Author display with "et al." abbreviation for 3+ authors
  - Clickable DOI links to original papers
- AI-Based Typo Checker (SPEC-TYPOCHECK-001)
  - Multi-provider support (Claude, OpenAI, Gemini)
  - Korean text typo checking (spelling, spacing, particles, loanwords)
  - Smart text chunking for long documents (up to 100,000 characters)
  - HTML/PDF report generation
  - Real-time progress tracking
- System Prompt Management (SPEC-SYSPROMPT-001)
  - Admin interface for managing AI provider system prompts
  - Support for Claude, Gemini, and OpenAI providers
  - Database persistence with automatic fallback to defaults
  - Real-time prompt updates across all AI operations

## System Architecture

```
┌─────────────┐     HTTP/REST     ┌──────────────┐     SQL      ┌──────────────┐
│   React     │ ←──────────────→  │   Flask      │ ←─────────→  │  PostgreSQL  │
│  Frontend   │                   │   Backend    │              │   Database   │
│  (Vite)     │                   │   (API)      │              │              │
└─────────────┘                   └──────────────┘              └──────────────┘
     │                                   │
     │                                   ├── PDF Processing
     │                                   ├── JWT Authentication
     │                                   └── File Storage
     │
     └── React Router, Zustand, Axios, Tailwind CSS
```

## Technology Stack

**Backend:**
- Flask >= 3.0
- PostgreSQL
- Flask-SQLAlchemy
- PyJWT for authentication
- pdfplumber for PDF text extraction
- requests for CrossRef API integration
- anthropic for Claude AI integration
- openai for OpenAI integration
- google-generativeai for Gemini integration
- weasyprint for PDF report generation

**Frontend:**
- React 19.2
- TypeScript
- Vite (build tool)
- React Router (navigation)
- Zustand (state management)
- Axios (HTTP client)
- Tailwind CSS (styling)
- Heroicons (icons)

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- PostgreSQL

### Backend Installation

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Create database:
```bash
createdb pdf_search_dev
createdb pdf_search_test
```

5. Run migrations:
```bash
flask db upgrade
```

6. Start development server:
```bash
python main.py
```

The backend will run on `http://localhost:5050` by default.

### Frontend Installation

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment:
```bash
# Create .env file (optional)
# VITE_API_BASE_URL=http://localhost:5050
```

4. Start development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:5173` by default.

## Running the Application

### Development Mode

1. **Start Backend** (Terminal 1):
```bash
cd backend
source venv/bin/activate  # Linux/macOS
python main.py
```

2. **Start Frontend** (Terminal 2):
```bash
cd frontend
npm run dev
```

3. **Access Application**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:5050
- API Documentation: http://localhost:5050/api/docs (if Swagger enabled)

### Production Build

1. **Build Frontend**:
```bash
cd frontend
npm run build
```

The production files will be generated in `frontend/dist/`.

2. **Serve Frontend** (multiple options):
```bash
# Option 1: Using Vite preview
npm run preview

# Option 2: Using a static file server
npx serve -s dist -l 3000

# Option 3: Using Python's HTTP server
cd dist
python -m http.server 3000
```

### Default User Accounts

The application comes with default test accounts:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Administrator |
| user1 | user123 | Regular User |

**Note**: Change these passwords in production!

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/auth/login | No | Login, returns JWT token |
| POST | /api/auth/logout | Yes | Logout, blacklists token |
| GET | /api/auth/me | Yes | Current user info |
| GET | /api/documents | Yes | Document list (owner filter) |
| POST | /api/documents | Yes | PDF upload (202 Accepted) |
| GET | /api/documents/{id} | Yes | Document detail (owner check) |
| DELETE | /api/documents/{id} | Yes | Delete document (owner check) |
| GET | /api/documents/{id}/file | Yes | PDF download (Range support) |
| POST | /api/typo-checker | Yes | Check text for typos |
| GET | /api/typo-checker/providers | Yes | List available AI providers |
| GET | /api/typo-checker/{id}/report | Yes | Download HTML/PDF report |
| GET | /api/admin/system-prompts | Yes (Admin) | List all system prompts |
| GET | /api/admin/system-prompts/{provider} | Yes (Admin) | Get specific provider prompt |
| PUT | /api/admin/system-prompts/{provider} | Yes (Admin) | Update system prompt |
| POST | /api/admin/system-prompts/{provider}/reset | Yes (Admin) | Reset to default prompt |

## Testing

```bash
cd backend
pytest --cov=app --cov-report=html
```

## Project Structure

```
pdf_quick_search/
├── backend/                  # Flask backend
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── utils/           # Utilities (JWT, validation)
│   │   └── storage/         # PDF file storage
│   ├── tests/               # Pytest tests
│   ├── migrations/          # Database migrations
│   ├── main.py              # Application entry point
│   └── requirements.txt     # Python dependencies
│
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── admin/       # Admin-specific components
│   │   │   │   └── SystemPromptEditor.tsx
│   │   │   ├── auth/        # Authentication components
│   │   │   ├── common/      # Shared UI components
│   │   │   ├── documents/   # Document management
│   │   │   ├── search/      # Search functionality
│   │   │   ├── typo/         # Typo checker components
│   │   │   └── viewer/      # PDF viewer
│   │   ├── pages/           # Page components
│   │   │   ├── LoginPage.tsx
│   │   │   ├── SearchPage.tsx
│   │   │   ├── DocumentsPage.tsx
│   │   │   └── AdminPage.tsx
│   │   ├── store/           # Zustand state management
│   │   ├── api/             # API client (Axios)
│   │   └── App.tsx          # Main app component
│   ├── public/              # Static assets
│   ├── package.json         # Node.js dependencies
│   └── vite.config.ts       # Vite configuration
│
└── README.md                # This file
```

## Key Features Detail

### Search Functionality
- Full-text search across all PDF documents
- Real-time search suggestions
- Filename autocomplete
- Context-aware search results with highlighted snippets
- PDF text extraction during upload

### Document Management
- Secure PDF upload with progress tracking
- Document listing with status badges
- Download with Range support (streaming)
- User-based document isolation
- Soft delete with ownership verification

### User Management (Admin)
- Create/edit/delete users
- Role-based access control (Admin/User)
- Password reset functionality
- User status management (active/inactive)

### Security
- JWT-based authentication
- Token blacklist on logout
- Owner-based authorization
- Protected routes (frontend & backend)
- Secure password storage
