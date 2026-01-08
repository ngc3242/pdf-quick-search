import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRightOnRectangleIcon,
  PlusIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import { Button, Modal } from '@/components/common';
import { DocumentList, UploadDialog } from '@/components/documents';
import { SearchInput, SearchResults } from '@/components/search';
import { PDFViewer } from '@/components/viewer';
import { useAuthStore, useDocumentStore } from '@/store';
import type { Document } from '@/types';

export function DocumentsPage() {
  const navigate = useNavigate();
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
  } = useDocumentStore();

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Document | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [viewerDoc, setViewerDoc] = useState<Document | null>(null);
  const [viewerPage, setViewerPage] = useState(1);
  const [localSearchQuery, setLocalSearchQuery] = useState('');

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleUpload = async (file: File) => {
    await uploadDocument(file);
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
      search(query);
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

  const handleSearchResultClick = (doc: Document, pageNumber: number) => {
    setViewerDoc(doc);
    setViewerPage(pageNumber);
  };

  const handlePageChange = (newPage: number) => {
    fetchDocuments(newPage);
  };

  const isAdmin = user?.role === 'admin';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-900">내 문서</h1>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-600">{user?.name}</span>
              {isAdmin && (
                <button
                  onClick={() => navigate('/admin')}
                  className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
                  title="관리자"
                >
                  <Cog6ToothIcon className="h-5 w-5" />
                </button>
              )}
              <button
                onClick={handleLogout}
                className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
                title="로그아웃"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-6">
        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="flex-1">
            <SearchInput
              value={localSearchQuery}
              onChange={setLocalSearchQuery}
              onSearch={handleSearch}
              onClear={handleClearSearch}
              isSearching={isSearching}
            />
          </div>
          <Button onClick={() => setIsUploadOpen(true)}>
            <PlusIcon className="h-5 w-5 mr-1" />
            PDF 업로드
          </Button>
        </div>

        {/* Content */}
        {searchQuery ? (
          <SearchResults
            results={searchResults}
            total={searchTotal}
            query={searchQuery}
            isSearching={isSearching}
            onDocumentClick={handleSearchResultClick}
          />
        ) : (
          <>
            <DocumentList
              documents={documents}
              isLoading={isLoading}
              onView={handleViewDocument}
              onDelete={setDeleteTarget}
            />

            {/* Pagination */}
            {pages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-6">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => handlePageChange(page - 1)}
                >
                  이전
                </Button>
                <span className="text-sm text-gray-600">
                  {page} / {pages}
                </span>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page >= pages}
                  onClick={() => handlePageChange(page + 1)}
                >
                  다음
                </Button>
              </div>
            )}
          </>
        )}
      </main>

      {/* Upload Dialog */}
      <UploadDialog
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUpload={handleUpload}
      />

      {/* Delete Confirmation Dialog */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="문서 삭제"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            이 문서를 삭제하시겠습니까?
            <br />
            <span className="font-medium text-gray-900">
              {deleteTarget?.original_filename}
            </span>
          </p>
          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              onClick={() => setDeleteTarget(null)}
              disabled={isDeleting}
            >
              취소
            </Button>
            <Button
              variant="danger"
              onClick={handleDelete}
              isLoading={isDeleting}
            >
              삭제
            </Button>
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
