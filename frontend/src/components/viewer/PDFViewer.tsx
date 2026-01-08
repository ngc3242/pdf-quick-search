import { useState, useEffect, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import {
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  PlusIcon,
  MinusIcon,
  ArrowsPointingOutIcon,
} from '@heroicons/react/24/outline';
import { Button } from '@/components/common';
import type { Document as DocType } from '@/types';

import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PDFViewerProps {
  document: DocType;
  initialPage?: number;
  onClose: () => void;
}

export function PDFViewer({ document: pdfDocument, initialPage = 1, onClose }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(initialPage);
  const [scale, setScale] = useState<number>(1.0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const token = localStorage.getItem('access_token');
  const pdfUrl = `/api/documents/${pdfDocument.id}/file`;

  // Close on escape key and hide scroll
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleEscape);
    window.document.body.style.overflow = 'hidden';

    return () => {
      window.removeEventListener('keydown', handleEscape);
      window.document.body.style.overflow = '';
    };
  }, [onClose]);

  const goToPrevPage = useCallback(() => {
    setPageNumber((prev) => Math.max(1, prev - 1));
  }, []);

  const goToNextPage = useCallback(() => {
    setPageNumber((prev) => Math.min(numPages, prev + 1));
  }, [numPages]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        goToPrevPage();
      } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        goToNextPage();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [goToPrevPage, goToNextPage]);

  const onDocumentLoadSuccess = ({ numPages: pages }: { numPages: number }) => {
    setNumPages(pages);
    setIsLoading(false);
    // Validate initial page number
    if (initialPage > pages) {
      setPageNumber(1);
    }
  };

  const onDocumentLoadError = (err: Error) => {
    console.error('PDF load error:', err);
    setError('PDF를 불러오는데 실패했습니다');
    setIsLoading(false);
  };

  const zoomIn = () => {
    setScale((prev) => Math.min(3, prev + 0.25));
  };

  const zoomOut = () => {
    setScale((prev) => Math.max(0.5, prev - 0.25));
  };

  const resetZoom = () => {
    setScale(1.0);
  };

  const handlePageInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value >= 1 && value <= numPages) {
      setPageNumber(value);
    }
  };

  // Build file object with auth headers
  const fileOptions = {
    url: pdfUrl,
    httpHeaders: {
      Authorization: `Bearer ${token}`,
    },
  };

  return (
    <div className="fixed inset-0 z-50 bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-800">
        <div className="flex items-center gap-4">
          <h2 className="text-white font-medium truncate max-w-md">
            {pdfDocument.original_filename}
          </h2>
        </div>

        <div className="flex items-center gap-2">
          {/* Zoom controls */}
          <div className="flex items-center gap-1 mr-4">
            <button
              onClick={zoomOut}
              className="p-2 rounded-lg text-gray-300 hover:bg-gray-700 transition-colors"
              title="축소"
            >
              <MinusIcon className="h-5 w-5" />
            </button>
            <button
              onClick={resetZoom}
              className="px-2 py-1 text-sm text-gray-300 hover:bg-gray-700 rounded-lg transition-colors"
              title="원본 크기"
            >
              {Math.round(scale * 100)}%
            </button>
            <button
              onClick={zoomIn}
              className="p-2 rounded-lg text-gray-300 hover:bg-gray-700 transition-colors"
              title="확대"
            >
              <PlusIcon className="h-5 w-5" />
            </button>
            <button
              onClick={resetZoom}
              className="p-2 rounded-lg text-gray-300 hover:bg-gray-700 transition-colors"
              title="맞춤"
            >
              <ArrowsPointingOutIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Page navigation */}
          <div className="flex items-center gap-2 mr-4">
            <button
              onClick={goToPrevPage}
              disabled={pageNumber <= 1}
              className="p-2 rounded-lg text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeftIcon className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-1 text-gray-300">
              <input
                type="number"
                min={1}
                max={numPages}
                value={pageNumber}
                onChange={handlePageInputChange}
                className="w-12 px-2 py-1 text-center bg-gray-700 border border-gray-600 rounded text-white text-sm"
              />
              <span className="text-sm">/ {numPages}</span>
            </div>
            <button
              onClick={goToNextPage}
              disabled={pageNumber >= numPages}
              className="p-2 rounded-lg text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRightIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Close button */}
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-300 hover:bg-gray-700 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-auto bg-gray-700 flex items-center justify-center p-4">
        {error ? (
          <div className="text-center">
            <p className="text-red-400 mb-4">{error}</p>
            <Button variant="secondary" onClick={onClose}>
              닫기
            </Button>
          </div>
        ) : (
          <Document
            file={fileOptions}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading={
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4" />
                <p className="text-gray-300">PDF 로딩 중...</p>
              </div>
            }
            className="flex justify-center"
          >
            {!isLoading && (
              <Page
                pageNumber={pageNumber}
                scale={scale}
                loading={
                  <div className="flex items-center justify-center h-96">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white" />
                  </div>
                }
                className="shadow-2xl"
                renderTextLayer={false}
                renderAnnotationLayer={false}
              />
            )}
          </Document>
        )}
      </div>
    </div>
  );
}
