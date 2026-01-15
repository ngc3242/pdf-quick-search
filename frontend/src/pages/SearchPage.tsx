/**
 * Search Page - Home page with search functionality
 * Provides file name autocomplete and full-text search
 */
import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { SearchResults, FileNameAutocomplete } from '@/components/search';
import { PDFViewer } from '@/components/viewer';
import { useAuthStore, useDocumentStore } from '@/store';
import type { Document } from '@/types';

export function SearchPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, logout } = useAuthStore();
  const {
    documents,
    fetchDocuments,
    searchQuery,
    searchResults,
    searchTotal,
    isSearching,
    search,
    clearSearch,
  } = useDocumentStore();

  const isAdmin = user?.role === 'admin';

  const [viewerDoc, setViewerDoc] = useState<Document | null>(null);
  const [viewerPage, setViewerPage] = useState(1);
  const [localSearchQuery, setLocalSearchQuery] = useState('');

  // Track if we've already handled URL params (prevent re-processing)
  const handledParamsRef = useRef<string | null>(null);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Handle URL params for auto-opening PDF (from new tab link)
  useEffect(() => {
    const docIdParam = searchParams.get('docId');
    const pageParam = searchParams.get('page');
    const queryParam = searchParams.get('query');

    // Skip if no docId
    if (!docIdParam) return;

    // Skip if documents haven't loaded yet
    if (documents.length === 0) return;

    const paramKey = `${docIdParam}-${pageParam}-${queryParam}`;

    // Skip if already handled this exact param combination
    if (handledParamsRef.current === paramKey) return;

    const docId = parseInt(docIdParam, 10);
    const pageNumber = pageParam ? parseInt(pageParam, 10) : 1;

    if (!isNaN(docId)) {
      // Find the document and open viewer
      const doc = documents.find((d) => d.id === docId);
      if (doc) {
        // Mark as handled only after we found the document
        handledParamsRef.current = paramKey;

        if (doc.extraction_status === 'completed') {
          // Use setTimeout to avoid synchronous setState in effect
          setTimeout(() => {
            setViewerDoc(doc);
            setViewerPage(pageNumber);
            // Set search query if provided
            if (queryParam) {
              setLocalSearchQuery(queryParam);
              search(queryParam);
            }
          }, 0);
        } else {
          alert('이 문서는 아직 인덱싱 중입니다.');
        }
      }
    }
  }, [searchParams, documents, search]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleSearch = useCallback(
    (query: string) => {
      if (query.trim().length >= 2) {
        search(query);
      }
    },
    [search]
  );

  const handleClearSearch = useCallback(() => {
    clearSearch();
    setLocalSearchQuery('');
  }, [clearSearch]);

  // Handle file selection from autocomplete
  const handleAutocompleteSelect = useCallback((document: Document) => {
    if (document.extraction_status !== 'completed') {
      alert('이 문서는 아직 인덱싱 중입니다. 완료 후 다시 시도해주세요.');
      return;
    }
    setViewerDoc(document);
    setViewerPage(1);
  }, []);

  // Open PDF in new tab when clicking search result (like SARA)
  const handleSearchResultClick = useCallback(
    (doc: Document, pageNumber: number) => {
      // Build URL with query params
      const params = new URLSearchParams();
      params.set('docId', String(doc.id));
      params.set('page', String(pageNumber));
      if (searchQuery) {
        params.set('query', searchQuery);
      }

      // Open main page in new tab with docId param
      window.open(`${window.location.origin}/?${params.toString()}`, '_blank');
    },
    [searchQuery]
  );

  // Extract matching pages for the currently viewed document from search results
  const matchingPages = useMemo(() => {
    if (!viewerDoc || !searchResults.length) return [];

    const pages = searchResults
      .filter((r) => r.document.id === viewerDoc.id)
      .map((r) => r.page_number);

    return [...new Set(pages)].sort((a, b) => a - b);
  }, [viewerDoc, searchResults]);

  return (
    <div className="min-h-screen bg-background-light flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white border-b border-[#e5e7eb] shadow-sm">
        <div className="flex items-center justify-between h-16 px-4 lg:px-10 max-w-[1400px] mx-auto w-full">
          {/* Logo - clickable to home */}
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-3 hover:opacity-80 transition-opacity"
          >
            <div className="size-10 rounded-lg bg-primary flex items-center justify-center text-white shadow-sm">
              <span className="material-symbols-outlined text-2xl">picture_as_pdf</span>
            </div>
            <h2 className="text-text-primary text-lg font-bold leading-tight tracking-[-0.015em] hidden sm:block">
              PDF Quick Search
            </h2>
          </button>

          {/* Global Search (Full-text) */}
          <div className="hidden md:flex flex-1 max-w-[480px] px-8">
            <label className="flex flex-col w-full !h-10">
              <div className="flex w-full flex-1 items-stretch rounded-lg h-full ring-1 ring-[#dbe0e6] focus-within:ring-2 focus-within:ring-primary overflow-hidden">
                <div className="text-text-secondary flex border-none bg-[#f9fafb] items-center justify-center pl-4 rounded-l-lg border-r-0">
                  {isSearching ? (
                    <span className="material-symbols-outlined text-[20px] text-primary animate-spin">progress_activity</span>
                  ) : (
                    <span className="material-symbols-outlined text-[20px]">search</span>
                  )}
                </div>
                <input
                  className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg rounded-l-none text-text-primary focus:outline-0 border-none bg-[#f9fafb] h-full placeholder:text-text-secondary px-3 text-sm font-normal leading-normal"
                  placeholder="전문 검색 (문서 내용에서 검색)..."
                  value={localSearchQuery}
                  onChange={(e) => setLocalSearchQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSearch(localSearchQuery);
                    }
                    if (e.key === 'Escape') {
                      handleClearSearch();
                    }
                  }}
                />
                {localSearchQuery && (
                  <button
                    onClick={handleClearSearch}
                    className="flex items-center justify-center px-3 text-text-secondary hover:text-text-primary transition-colors"
                  >
                    <span className="material-symbols-outlined text-[20px]">close</span>
                  </button>
                )}
              </div>
            </label>
          </div>

          <div className="flex items-center justify-end gap-4 lg:gap-8">
            <nav className="hidden lg:flex items-center gap-6">
              <button
                onClick={() => navigate('/documents')}
                className="text-text-primary text-sm font-medium hover:text-primary transition-colors"
              >
                Documents
              </button>
              <button
                onClick={() => navigate('/typo-checker')}
                className="text-text-primary text-sm font-medium hover:text-primary transition-colors"
              >
                맞춤법 검사
              </button>
              {isAdmin && (
                <button
                  onClick={() => navigate('/admin')}
                  className="text-text-primary text-sm font-medium hover:text-primary transition-colors"
                >
                  Users
                </button>
              )}
            </nav>
            <button
              onClick={handleLogout}
              className="flex items-center justify-center rounded-full size-10 hover:bg-[#f0f2f4] transition-colors text-text-primary"
              title="Logout"
            >
              <span className="material-symbols-outlined">logout</span>
            </button>
            <div className="bg-primary text-white rounded-full size-10 flex items-center justify-center text-sm font-bold cursor-pointer">
              {user?.name?.charAt(0).toUpperCase() || 'U'}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full max-w-[1200px] mx-auto px-4 lg:px-10 py-8">
        {/* Page Heading */}
        <div className="flex flex-col gap-2 mb-8">
          <h1 className="text-text-primary text-3xl font-black leading-tight tracking-[-0.033em]">
            PDF Quick Search
          </h1>
          <p className="text-text-secondary text-base font-normal">
            파일명 또는 문서 내용으로 빠르게 검색하세요.
          </p>
        </div>

        {/* Search Section */}
        <div className="bg-white rounded-xl border border-[#dbe0e6] shadow-sm p-6 mb-6 space-y-6">
          {/* File Name Autocomplete (Client-Side) */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              파일 선택
            </label>
            <FileNameAutocomplete
              documents={documents}
              onSelect={handleAutocompleteSelect}
            />
          </div>

          {/* Full-Text Search (Server-Side) */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              전문 검색
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                {isSearching ? (
                  <span className="material-symbols-outlined text-[20px] text-primary animate-spin">
                    progress_activity
                  </span>
                ) : (
                  <span className="material-symbols-outlined text-text-secondary text-[20px]">search</span>
                )}
              </div>
              <input
                className="block w-full pl-10 pr-10 py-3 border border-[#dbe0e6] rounded-lg bg-white text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary text-base"
                placeholder="문서 내용에서 검색..."
                type="text"
                value={localSearchQuery}
                onChange={(e) => setLocalSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSearch(localSearchQuery);
                  if (e.key === 'Escape') handleClearSearch();
                }}
              />
              {localSearchQuery && (
                <button
                  onClick={handleClearSearch}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-text-secondary hover:text-text-primary transition-colors"
                >
                  <span className="material-symbols-outlined text-[20px]">close</span>
                </button>
              )}
            </div>
            {localSearchQuery.length > 0 && localSearchQuery.length < 2 && (
              <p className="mt-1 text-xs text-text-secondary pl-1">2자 이상 입력하세요</p>
            )}
          </div>
        </div>

        {/* Search Results */}
        {searchQuery && (
          <SearchResults
            results={searchResults}
            total={searchTotal}
            query={searchQuery}
            isSearching={isSearching}
            onDocumentClick={handleSearchResultClick}
          />
        )}
      </main>

      {/* PDF Viewer */}
      {viewerDoc && (
        <PDFViewer
          document={viewerDoc}
          initialPage={viewerPage}
          searchQuery={searchQuery}
          matchingPages={matchingPages}
          onClose={() => setViewerDoc(null)}
        />
      )}
    </div>
  );
}
