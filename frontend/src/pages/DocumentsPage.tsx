/**
 * Documents Page - File list management
 * Upload, view, and delete PDF documents
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Modal } from '@/components/common';
import { PDFViewer } from '@/components/viewer';
import { AuthorDisplay, DOILink } from '@/components/documents';
import { useAuthStore, useDocumentStore } from '@/store';
import type { Document, ExtractionStatus, MetadataStatus } from '@/types';

export function DocumentsPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const {
    documents,
    isLoading,
    fetchDocuments,
    uploadDocument,
    deleteDocument,
    page,
    pages,
    total,
  } = useDocumentStore();

  const isAdmin = user?.role === 'admin';

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Document | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [viewerDoc, setViewerDoc] = useState<Document | null>(null);
  const [viewerPage, setViewerPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;
    const pdfFiles = Array.from(files).filter(f => f.type === 'application/pdf');
    setUploadFiles(prev => [...prev, ...pdfFiles]);
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

  const handleViewDocument = (doc: Document) => {
    if (doc.extraction_status !== 'completed') {
      alert('이 문서는 아직 인덱싱 중입니다.');
      return;
    }
    setViewerDoc(doc);
    setViewerPage(1);
  };

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
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const pdfFiles = Array.from(files).filter(f => f.type === 'application/pdf');
      setUploadFiles(prev => [...prev, ...pdfFiles]);
    }
  };

  const filteredDocuments = statusFilter
    ? documents.filter((doc) => doc.extraction_status === statusFilter)
    : documents;

  const getStatusBadge = (status: ExtractionStatus) => {
    const styles: Record<ExtractionStatus, string> = {
      completed: 'bg-green-50 text-green-700 border-green-200',
      processing: 'bg-blue-50 text-blue-700 border-blue-200',
      pending: 'bg-yellow-50 text-yellow-700 border-yellow-200',
      failed: 'bg-red-50 text-red-700 border-red-200',
    };
    const labels: Record<ExtractionStatus, string> = {
      completed: 'Completed',
      processing: 'Processing',
      pending: 'Pending',
      failed: 'Failed',
    };
    return (
      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${styles[status]}`}>
        <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
          status === 'completed' ? 'bg-green-500' :
          status === 'processing' ? 'bg-blue-500 animate-pulse' :
          status === 'pending' ? 'bg-yellow-500' : 'bg-red-500'
        }`} />
        {labels[status]}
      </span>
    );
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Metadata loading indicator for CrossRef metadata status
  const getMetadataStatusIndicator = (status: MetadataStatus | null) => {
    if (!status || status === 'pending') {
      return null;
    }
    if (status === 'processing') {
      return (
        <span className="inline-flex items-center gap-1 text-xs text-blue-600" title="Fetching metadata...">
          <span className="material-symbols-outlined text-[14px] animate-spin">progress_activity</span>
        </span>
      );
    }
    return null;
  };

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

          <div className="flex items-center justify-end gap-4 lg:gap-8">
            <nav className="hidden lg:flex items-center gap-6">
              <button
                onClick={() => navigate('/documents')}
                className="text-primary text-sm font-medium"
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
                  <th className="px-4 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider w-[22%]">
                    File Name
                  </th>
                  <th className="px-4 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider w-[6%]">
                    Year
                  </th>
                  <th className="px-4 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider w-[12%]">
                    First Author
                  </th>
                  <th className="px-4 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider w-[12%]">
                    Co-Authors
                  </th>
                  <th className="px-4 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider w-[14%]">
                    Journal
                  </th>
                  <th className="px-4 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider w-[12%]">
                    DOI
                  </th>
                  <th className="px-4 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider w-[8%]">
                    Status
                  </th>
                  <th className="px-4 py-4 text-xs font-semibold text-text-secondary uppercase tracking-wider text-right w-[8%]">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#dbe0e6]">
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center">
                      <span className="material-symbols-outlined text-4xl text-text-secondary animate-spin">
                        progress_activity
                      </span>
                      <p className="mt-2 text-text-secondary">Loading documents...</p>
                    </td>
                  </tr>
                ) : filteredDocuments.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center">
                      <span className="material-symbols-outlined text-4xl text-text-secondary">folder_off</span>
                      <p className="mt-2 text-text-secondary">No documents found</p>
                    </td>
                  </tr>
                ) : (
                  filteredDocuments.map((doc) => (
                    <tr key={doc.id} className="hover:bg-[#f9fafb] transition-colors group">
                      {/* File Name */}
                      <td className="px-4 py-4">
                        <button
                          onClick={() => handleViewDocument(doc)}
                          className="flex items-center gap-3 text-left hover:text-primary transition-colors"
                          disabled={doc.extraction_status !== 'completed'}
                        >
                          <div className="size-9 rounded-lg bg-red-50 flex items-center justify-center flex-shrink-0">
                            <span className="material-symbols-outlined text-red-500 text-[20px]">picture_as_pdf</span>
                          </div>
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-text-primary truncate max-w-[200px]">
                              {doc.original_filename}
                            </p>
                            <p className="text-xs text-text-secondary">
                              {doc.page_count ? `${doc.page_count}p` : ''} {doc.file_size_bytes ? formatFileSize(doc.file_size_bytes) : ''}
                            </p>
                          </div>
                        </button>
                      </td>
                      {/* Publication Year (A) */}
                      <td className="px-4 py-4 text-sm text-text-secondary">
                        <div className="flex items-center gap-1">
                          {doc.publication_year || '-'}
                          {getMetadataStatusIndicator(doc.metadata_status)}
                        </div>
                      </td>
                      {/* First Author (B) */}
                      <td className="px-4 py-4 text-sm text-text-primary">
                        <AuthorDisplay
                          firstAuthor={doc.first_author}
                          coAuthors={doc.co_authors}
                          type="first"
                        />
                      </td>
                      {/* Co-Authors (C) */}
                      <td className="px-4 py-4 text-sm text-text-primary">
                        <AuthorDisplay
                          firstAuthor={doc.first_author}
                          coAuthors={doc.co_authors}
                          type="co"
                        />
                      </td>
                      {/* Journal Name (D) */}
                      <td className="px-4 py-4 text-sm text-text-secondary">
                        <span className="truncate block max-w-[150px]" title={doc.journal_name || doc.publisher || undefined}>
                          {doc.journal_name || doc.publisher || '-'}
                        </span>
                      </td>
                      {/* DOI Link (E) */}
                      <td className="px-4 py-4 text-sm">
                        <DOILink doi={doc.doi} doiUrl={doc.doi_url} />
                      </td>
                      {/* Status */}
                      <td className="px-4 py-4">
                        {getStatusBadge(doc.extraction_status)}
                      </td>
                      {/* Actions */}
                      <td className="px-4 py-4 text-right">
                        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => handleViewDocument(doc)}
                            className="p-1.5 rounded-lg text-text-secondary hover:text-primary hover:bg-primary/10 transition-colors"
                            title="View"
                            disabled={doc.extraction_status !== 'completed'}
                          >
                            <span className="material-symbols-outlined text-[18px]">visibility</span>
                          </button>
                          <button
                            onClick={() => setDeleteTarget(doc)}
                            className="p-1.5 rounded-lg text-text-secondary hover:text-red-500 hover:bg-red-50 transition-colors"
                            title="Delete"
                          >
                            <span className="material-symbols-outlined text-[18px]">delete</span>
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
            <div className="flex items-center justify-between px-6 py-4 border-t border-[#dbe0e6] bg-[#f9fafb]">
              <p className="text-sm text-text-secondary">
                Showing <span className="font-medium">{(page - 1) * 20 + 1}</span> to{' '}
                <span className="font-medium">{Math.min(page * 20, total)}</span> of{' '}
                <span className="font-medium">{total}</span> documents
              </p>
              <div className="flex items-center gap-2">
                <button
                  className="px-3 py-1 rounded-md border border-[#dbe0e6] text-sm font-medium text-text-primary hover:bg-[#f9fafb] disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={page <= 1}
                  onClick={() => handlePageChange(page - 1)}
                >
                  Previous
                </button>
                {Array.from({ length: Math.min(3, pages) }, (_, i) => i + 1).map((p) => (
                  <button
                    key={p}
                    className={`px-3 py-1 rounded-md text-sm font-medium ${
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
              className="px-4 py-2 rounded-lg bg-red-500 text-white font-medium text-sm hover:bg-red-600 transition-colors disabled:opacity-50"
              disabled={isDeleting}
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>
      </Modal>

      {/* PDF Viewer */}
      {viewerDoc && (
        <PDFViewer
          document={viewerDoc}
          initialPage={viewerPage}
          onClose={() => setViewerDoc(null)}
        />
      )}
    </div>
  );
}
