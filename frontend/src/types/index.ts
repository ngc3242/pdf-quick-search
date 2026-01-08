// User types
export interface User {
  id: string;
  email: string;
  name: string;
  phone: string | null;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
}

// Document types
export type ExtractionStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Document {
  id: number;
  owner_id: string;
  filename: string;
  original_filename: string;
  file_size_bytes: number | null;
  mime_type: string;
  page_count: number | null;
  extraction_status: ExtractionStatus;
  extraction_error: string | null;
  uploaded_at: string;
  extraction_completed_at: string | null;
  is_active: boolean;
}

export interface DocumentsResponse {
  documents: Document[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Search types
export interface SearchResult {
  document: Document;
  page_number: number;
  snippet: string;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  limit: number;
  offset: number;
}

// Auth types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  user: User;
}

// Admin types
export interface UserWithDocuments extends User {
  document_count?: number;
}

export interface CreateUserRequest {
  email: string;
  name: string;
  password: string;
  phone?: string;
  role?: 'admin' | 'user';
}

export interface UpdateUserRequest {
  name?: string;
  phone?: string;
  role?: 'admin' | 'user';
  is_active?: boolean;
}

// API Error type
export interface ApiError {
  error: string;
}
