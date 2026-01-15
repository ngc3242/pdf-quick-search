# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- AI-Based Korean Typo Checker feature (SPEC-TYPOCHECK-001)
  - POST /api/typo-checker - Check text for typos using AI providers
  - GET /api/typo-checker/providers - List available AI providers
  - GET /api/typo-checker/{check_id}/report - Download HTML/PDF reports
  - Support for Claude, OpenAI, and Gemini AI providers
  - Text chunking for documents up to 100,000 characters
  - Progress tracking during long text analysis
  - TypoCheckerPage with TextInput, ProviderSelector, ResultDisplay, ReportDownload, ProgressIndicator components
  - Zustand store for typo checker state management
  - Comprehensive test coverage (290 backend + 112 frontend tests)

## [1.0.0] - 2026-01-09

### Added
- CrossRef DOI metadata integration (SPEC-CROSSREF-001)
  - Automatic DOI extraction from PDF documents
  - CrossRef API integration with caching (7-day TTL)
  - Author display with "et al." abbreviation for 3+ authors
  - Clickable DOI links to original papers
- Initial PDF Quick Search functionality
  - User authentication with JWT tokens
  - PDF document upload and management
  - User-based document isolation
  - Full-text search with PDF text extraction
  - Document download with Range support
  - Modern React UI with SARA-style design
  - Admin user management
