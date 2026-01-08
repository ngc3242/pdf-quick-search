# PDF Quick Search

PDF document management and search service with user isolation.

## Features

- User authentication with JWT tokens
- PDF document upload and management
- User-based document isolation
- Document download with Range support

## Technology Stack

- Flask >= 3.0
- PostgreSQL
- Flask-SQLAlchemy
- PyJWT for authentication

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL

### Installation

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate
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

## Testing

```bash
cd backend
pytest --cov=app --cov-report=html
```
