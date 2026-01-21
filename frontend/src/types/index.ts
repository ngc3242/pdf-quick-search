// User types
export type ApprovalStatus = 'pending' | 'approved' | 'rejected';

export interface User {
  id: string;
  email: string;
  name: string;
  phone: string | null;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  approval_status: ApprovalStatus;
  approved_at: string | null;
  approved_by_id: string | null;
  approval_reason: string | null;
}

// Document types
export type ExtractionStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type MetadataStatus = 'pending' | 'processing' | 'completed' | 'failed';

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
  // CrossRef metadata fields (SPEC-CROSSREF-001)
  doi: string | null;
  doi_url: string | null;
  publication_year: number | null;
  first_author: string | null;
  co_authors: string[] | null;
  journal_name: string | null;
  publisher: string | null;
  metadata_status: MetadataStatus | null;
  metadata_fetched_at: string | null;
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

export interface SignupRequest {
  email: string;
  name: string;
  phone: string;
  password: string;
}

export interface SignupResponse {
  message: string;
  user: {
    id: string;
    email: string;
    name: string;
    approval_status: 'pending' | 'approved' | 'rejected';
  };
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

// Typo Checker types (SPEC-TYPOCHECK-001)
export type TypoProvider = 'claude' | 'openai' | 'gemini';

export interface TypoIssue {
  original: string;
  corrected: string;
  position: {
    start: number;
    end: number;
  };
  type: 'spelling' | 'grammar' | 'punctuation' | 'style';
  explanation: string;
}

export interface TypoCheckResult {
  original_text: string;
  corrected_text: string;
  issues: TypoIssue[];
  provider: TypoProvider;
  processing_time_ms: number;
  chunk_count: number;
}

export interface TypoCheckRequest {
  text: string;
  provider: TypoProvider;
}

export interface TypoCheckProgress {
  current_chunk: number;
  total_chunks: number;
  percentage: number;
}

export interface ProviderAvailability {
  claude: boolean;
  openai: boolean;
  gemini: boolean;
}

// Typo History types (SPEC-HISTORY-001)
export interface TypoHistoryItem {
  id: number;
  original_text: string;
  corrected_text: string;
  issues: TypoIssue[];
  provider: TypoProvider;
  created_at: string;
  issue_count: number;
}

export interface TypoHistoryResponse {
  success: boolean;
  history: TypoHistoryItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// System Prompt types (SPEC-SYSPROMPT-001)
export interface SystemPrompt {
  provider: TypoProvider;
  prompt: string;
  is_active: boolean;
  is_custom: boolean;
  updated_at: string | null;
}

export interface SystemPromptsResponse {
  prompts: SystemPrompt[];
}

export interface UpdateSystemPromptRequest {
  prompt: string;
}

export interface ResetSystemPromptResponse {
  message: string;
  default_prompt: string;
}

// Storage Management types (SPEC-STORAGE-001)
export interface UserStorageUsage {
  user_id: string;
  user_name: string;
  user_email: string;
  document_count: number;
  total_size_bytes: number;
}

export interface StorageStatsResponse {
  total_documents: number;
  total_size_bytes: number;
  users: UserStorageUsage[];
}

export interface DiskUsageResponse {
  total_bytes: number;
  used_bytes: number;
  free_bytes: number;
  percentage_used: number;
}
