import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Modal } from '@/components/common';
import { SearchResults, FileNameAutocomplete } from '@/components/search';
import { PDFViewer } from '@/components/viewer';
import { useAuthStore, useDocumentStore } from '@/store';
import type { Document, ExtractionStatus } from '@/types';

export function DocumentsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, logout } = useAuthStore();
  const {
    documents,
    isLoading,
    fetchDocuments,
    uploadDocument,
    deleteDocument,
    searchQuery,
    searchResults,
    searchTotal,
    isSearching,
    search,
    clearSearch,
    page,
    pages,
    total,
  } = useDocumentStore();

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Document | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [viewerDoc, setViewerDoc] = useState<Document | null>(null);
  const [viewerPage, setViewerPage] = useState(1);
  const [localSearchQuery, setLocalSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
          setViewerDoc(doc);
          setViewerPage(pageNumber);
          // Set search query if provided
          if (queryParam) {
            setLocalSearchQuery(queryParam);
            search(queryParam);
          }
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

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;
    const pdfFiles = Array.from(files).filter(f => f.type === 'application/pdf');
    setUploadFiles(pdfFiles);
    if (pdfFiles.length > 0) {
      setIsUploadOpen(true);
    }
  };

  const handleUpload = async () => {
    if (uploadFiles.length === 0) return;
    setIsUploading(true);
    try {
      for (const file of uploadFiles) {
        await uploadDocument(file);
      }
      setUploadFiles([]);
      setIsUploadOpen(false);
      fetchDocuments();
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deleteDocument(deleteTarget.id);
      setDeleteTarget(null);
    } finally {
      setIsDeleting(false);
    }
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

  const handleViewDocument = (doc: Document) => {
    setViewerDoc(doc);
    setViewerPage(1);
  };

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

  // Extract matching pages for the currently viewed document from search results (for modal viewer)
  const matchingPages = useMemo(() => {
    if (!viewerDoc || !searchResults.length) return [];

    // Find all results for the current document and extract unique page numbers
    const pages = searchResults
      .filter((r) => r.document.id === viewerDoc.id)
      .map((r) => r.page_number);

    // Return unique sorted page numbers
    return [...new Set(pages)].sort((a, b) => a - b);
  }, [viewerDoc, searchResults]);

  const handlePageChange = (newPage: number) => {
    fetchDocuments(newPage);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const getStatusBadge = (status: ExtractionStatus) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 border border-green-200">
            <span className="size-1.5 rounded-full bg-green-500"></span>
            Completed
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary border border-blue-100">
            <span className="material-symbols-outlined text-[14px] animate-spin">progress_activity</span>
            Processing
          </span>
        );
      case 'pending':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
            <span className="size-1.5 rounded-full bg-gray-500"></span>
            Pending
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700 border border-red-200">
            <span className="material-symbols-outlined text-[14px]">error</span>
            Failed
          </span>
        );
      default:
        return null;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const filteredDocuments = statusFilter
    ? documents.filter(d => d.extraction_status === statusFilter)
    : documents;

  const isAdmin = user?.role === 'admin';

  return (
    <div className="bg-background-light min-h-screen font-display flex flex-col">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-50 bg-white border-b border-solid border-b-[#f0f2f4] w-full">
        <div className="flex items-center justify-between whitespace-nowrap px-4 lg:px-10 py-3 max-w-[1440px] mx-auto w-full">
          <div className="flex items-center gap-4 lg:gap-8">
            <div className="flex items-center gap-4 text-text-primary">
              <div className="size-8 flex items-center justify-center text-primary">
                <span className="material-symbols-outlined text-3xl">picture_as_pdf</span>
              </div>
              <h2 className="text-text-primary text-lg font-bold leading-tight tracking-[-0.015em] hidden sm:block">
                PDF Quick Search
              </h2>
            </div>
          </div>

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
                onClick={() => navigate('/')}
                className="text-text-primary text-sm font-medium hover:text-primary transition-colors"
              >
                Documents
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
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div className="flex flex-col gap-1">
            <h1 className="text-text-primary text-3xl font-black leading-tight tracking-[-0.033em]">My Documents</h1>
            <p className="text-text-secondary text-base font-normal">Manage, upload and organize your PDF files.</p>
          </div>
          <button
            type="button"
            onClick={() => setIsUploadOpen(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors shadow-sm"
          >
            <span className="material-symbols-outlined text-[20px]">add</span>
            파일 업로드
          </button>
        </div>

            {/* Search Section */}
            <div className="bg-white rounded-xl border border-[#dbe0e6] shadow-sm p-4 mb-6 space-y-4">
              {/* File Name Autocomplete (Client-Side) */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  파일 선택
                </label>
                <FileNameAutocomplete
                  documents={documents}
                  onSelect={handleAutocompleteSelect}
                />
              </div>

              {/* Full-Text Search (Server-Side) */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
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
                    className="block w-full pl-10 pr-10 py-2.5 border border-[#dbe0e6] rounded-lg bg-white text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary sm:text-sm"
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
                {isSearching && (
                  <p className="mt-1 text-xs text-primary pl-1">검색 중...</p>
                )}
              </div>
            </div>

            {/* Search Results (shown when there's a full-text query) */}
            {searchQuery && (
              <SearchResults
                results={searchResults}
                total={searchTotal}
                query={searchQuery}
                isSearching={isSearching}
                onDocumentClick={handleSearchResultClick}
              />
            )}

            {/* Toolbar (Filter & Refresh) */}
            <div className="flex flex-col sm:flex-row gap-4 mb-6 justify-between items-end sm:items-center">
              <div className="flex flex-1 w-full sm:max-w-[300px] gap-3">
                <div className="relative flex-1">
                  <select
                    className="block w-full pl-3 pr-10 py-2.5 border border-[#dbe0e6] rounded-lg bg-white text-text-primary focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary sm:text-sm appearance-none cursor-pointer"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                  >
                    <option value="">All Statuses</option>
                    <option value="completed">Completed</option>
                    <option value="processing">Processing</option>
                    <option value="pending">Pending</option>
                    <option value="failed">Failed</option>
                  </select>
                  <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                    <span className="material-symbols-outlined text-text-secondary">expand_more</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => fetchDocuments(page)}
                className="flex items-center gap-2 px-4 py-2.5 bg-white border border-[#dbe0e6] rounded-lg text-text-primary font-medium text-sm hover:bg-[#f9fafb] transition-colors shadow-sm"
              >
                <span className="material-symbols-outlined text-[20px]">refresh</span>
                <span>Refresh</span>
              </button>
            </div>

            {/* Documents Table */}
            <div className="bg-white rounded-xl border border-[#dbe0e6] shadow-sm overflow-hidden mb-8">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-[#f9fafb] border-b border-[#dbe0e6]">
                      <th className="px-6 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider w-[40%]">
                        File Name
                      </th>
                      <th className="px-6 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                        Date Uploaded
                      </th>
                      <th className="px-6 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                        Size
                      </th>
                      <th className="px-6 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider text-right">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#dbe0e6]">
                    {isLoading ? (
                      <tr>
                        <td colSpan={5} className="px-6 py-12 text-center">
                          <span className="material-symbols-outlined text-4xl text-text-secondary animate-spin">
                            progress_activity
                          </span>
                          <p className="mt-2 text-text-secondary">Loading documents...</p>
                        </td>
                      </tr>
                    ) : filteredDocuments.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-6 py-12 text-center">
                          <span className="material-symbols-outlined text-4xl text-text-secondary">folder_open</span>
                          <p className="mt-2 text-text-secondary">No documents found</p>
                        </td>
                      </tr>
                    ) : (
                      filteredDocuments.map((doc) => (
                        <tr
                          key={doc.id}
                          className="hover:bg-[#f9fafb] transition-colors group cursor-pointer"
                          onClick={() => doc.extraction_status === 'completed' && handleViewDocument(doc)}
                        >
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div
                                className={`size-10 rounded-lg flex items-center justify-center shrink-0 ${
                                  doc.extraction_status === 'failed'
                                    ? 'bg-gray-100 text-gray-400'
                                    : 'bg-red-50 text-red-600'
                                }`}
                              >
                                <span className="material-symbols-outlined">
                                  {doc.extraction_status === 'failed' ? 'description' : 'picture_as_pdf'}
                                </span>
                              </div>
                              <div className="flex flex-col min-w-0">
                                <p className="text-sm font-medium text-text-primary truncate max-w-[200px] sm:max-w-xs">
                                  {doc.original_filename}
                                </p>
                                {doc.page_count && (
                                  <p className="text-xs text-text-secondary">{doc.page_count} pages</p>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-text-secondary">
                            {formatDate(doc.uploaded_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-text-secondary font-mono">
                            {doc.file_size_bytes ? formatFileSize(doc.file_size_bytes) : '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">{getStatusBadge(doc.extraction_status)}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                className={`p-1.5 rounded-md transition-colors ${
                                  doc.extraction_status === 'completed'
                                    ? 'text-gray-500 hover:text-primary hover:bg-primary/10'
                                    : 'text-gray-400 cursor-not-allowed'
                                }`}
                                title="View"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (doc.extraction_status === 'completed') handleViewDocument(doc);
                                }}
                                disabled={doc.extraction_status !== 'completed'}
                              >
                                <span className="material-symbols-outlined text-[20px]">visibility</span>
                              </button>
                              <button
                                className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                                title="Delete"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setDeleteTarget(doc);
                                }}
                              >
                                <span className="material-symbols-outlined text-[20px]">delete</span>
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {pages > 1 && (
                <div className="px-6 py-4 border-t border-[#dbe0e6] flex items-center justify-between">
                  <p className="text-sm text-text-secondary hidden sm:block">
                    Showing <span className="font-medium text-text-primary">{(page - 1) * 20 + 1}</span> to{' '}
                    <span className="font-medium text-text-primary">{Math.min(page * 20, total)}</span> of{' '}
                    <span className="font-medium text-text-primary">{total}</span> results
                  </p>
                  <div className="flex items-center gap-2 mx-auto sm:mx-0">
                    <button
                      className="px-3 py-1 rounded-md border border-[#dbe0e6] text-sm font-medium text-text-secondary hover:bg-[#f9fafb] disabled:opacity-50 disabled:cursor-not-allowed"
                      disabled={page <= 1}
                      onClick={() => handlePageChange(page - 1)}
                    >
                      Previous
                    </button>
                    {Array.from({ length: Math.min(pages, 3) }, (_, i) => i + 1).map((p) => (
                      <button
                        key={p}
                        className={`size-8 rounded-md text-sm font-medium flex items-center justify-center transition-colors ${
                          p === page
                            ? 'bg-primary text-white'
                            : 'border border-[#dbe0e6] text-text-primary hover:bg-[#f9fafb]'
                        }`}
                        onClick={() => handlePageChange(p)}
                      >
                        {p}
                      </button>
                    ))}
                    {pages > 3 && <span className="text-text-secondary px-1">...</span>}
                    <button
                      className="px-3 py-1 rounded-md border border-[#dbe0e6] text-sm font-medium text-text-primary hover:bg-[#f9fafb] disabled:opacity-50 disabled:cursor-not-allowed"
                      disabled={page >= pages}
                      onClick={() => handlePageChange(page + 1)}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
      </main>

      {/* Upload Dialog */}
      <Modal isOpen={isUploadOpen} onClose={() => !isUploading && setIsUploadOpen(false)} title="파일 업로드" size="md">
        <div className="space-y-4">
          {/* Drop Zone */}
          <div
            className={`group relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed ${
              isDragOver
                ? 'border-primary bg-blue-50/50'
                : 'border-[#dbe0e6] hover:border-primary hover:bg-blue-50/30'
            } bg-white transition-all px-6 py-8 cursor-pointer`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => !isUploading && fileInputRef.current?.click()}
          >
            <div className="size-12 rounded-full bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
              <span className="material-symbols-outlined text-2xl">cloud_upload</span>
            </div>
            <div className="flex flex-col items-center gap-1 text-center">
              <p className="text-text-primary text-base font-medium">클릭 또는 드래그하여 업로드</p>
              <p className="text-text-secondary text-sm">PDF 파일만 가능 (최대 500MB)</p>
            </div>
            <input
              ref={fileInputRef}
              accept=".pdf"
              className="hidden"
              type="file"
              multiple
              onChange={(e) => handleFileSelect(e.target.files)}
              disabled={isUploading}
            />
          </div>

          {/* Selected Files List */}
          {uploadFiles.length > 0 && (
            <div className="max-h-48 overflow-y-auto">
              <p className="text-sm font-medium text-text-primary mb-2">
                선택된 파일 ({uploadFiles.length}개)
              </p>
              <div className="space-y-2">
                {uploadFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <span className="material-symbols-outlined text-red-500 flex-shrink-0">picture_as_pdf</span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-text-primary truncate">{file.name}</p>
                        <p className="text-xs text-text-secondary">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    {!isUploading && (
                      <button
                        onClick={() => setUploadFiles(uploadFiles.filter((_, i) => i !== index))}
                        className="text-gray-400 hover:text-red-500 transition-colors flex-shrink-0"
                      >
                        <span className="material-symbols-outlined text-[20px]">close</span>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2 border-t border-gray-100">
            <button
              onClick={() => {
                setUploadFiles([]);
                setIsUploadOpen(false);
              }}
              className="px-4 py-2 rounded-lg border border-[#dbe0e6] text-text-primary font-medium text-sm hover:bg-[#f9fafb] transition-colors"
              disabled={isUploading}
            >
              취소
            </button>
            <button
              onClick={handleUpload}
              className="px-4 py-2 rounded-lg bg-primary text-white font-medium text-sm hover:bg-blue-600 transition-colors disabled:opacity-50 inline-flex items-center gap-2"
              disabled={isUploading || uploadFiles.length === 0}
            >
              {isUploading ? (
                <>
                  <span className="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                  업로드 중...
                </>
              ) : (
                <>업로드 {uploadFiles.length > 0 && `(${uploadFiles.length})`}</>
              )}
            </button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Document" size="sm">
        <div className="space-y-4">
          <p className="text-text-secondary">
            Are you sure you want to delete this document?
            <br />
            <span className="font-medium text-text-primary">{deleteTarget?.original_filename}</span>
          </p>
          <div className="flex justify-end gap-3">
            <button
              onClick={() => setDeleteTarget(null)}
              className="px-4 py-2 rounded-lg border border-[#dbe0e6] text-text-primary font-medium text-sm hover:bg-[#f9fafb] transition-colors"
              disabled={isDeleting}
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              className="px-4 py-2 rounded-lg bg-red-600 text-white font-medium text-sm hover:bg-red-700 transition-colors disabled:opacity-50"
              disabled={isDeleting}
            >
              {isDeleting ? (
                <span className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                  Deleting...
                </span>
              ) : (
                'Delete'
              )}
            </button>
          </div>
        </div>
      </Modal>

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
