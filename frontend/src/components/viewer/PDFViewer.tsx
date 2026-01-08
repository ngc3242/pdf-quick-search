/**
 * PDF Viewer component
 * Based on SARA - SPEC-SEARCH-001
 *
 * Features:
 * - Page navigation (prev/next, direct input)
 * - Zoom controls
 * - Text selection
 * - Search highlighting with navigation
 */
import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
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

// CMap configuration for CJK (Korean, Japanese, Chinese) text rendering
const cMapOptions = {
  cMapUrl: `//unpkg.com/pdfjs-dist@${pdfjs.version}/cmaps/`,
  cMapPacked: true,
};

interface PDFViewerProps {
  document: DocType;
  initialPage?: number;
  searchQuery?: string;
  /** Pages that have search matches (sorted ascending) */
  matchingPages?: number[];
  onClose: () => void;
}

interface HighlightMatch {
  element: HTMLElement;
  index: number;
}

export function PDFViewer({
  document: pdfDocument,
  initialPage = 1,
  searchQuery,
  matchingPages = [],
  onClose,
}: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(initialPage);
  const [scale, setScale] = useState<number>(() => {
    // Load saved zoom level from localStorage
    const saved = localStorage.getItem('pdfViewerScale');
    return saved ? parseFloat(saved) : 1.0;
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search highlighting state
  const [highlights, setHighlights] = useState<HighlightMatch[]>([]);
  const [currentHighlightIndex, setCurrentHighlightIndex] = useState(0);
  const [pageRendered, setPageRendered] = useState(false);

  const pageInputRef = useRef<HTMLInputElement>(null);

  const token = localStorage.getItem('access_token');
  const pdfUrl = `/api/documents/${pdfDocument.id}/file`;

  // Save zoom level to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('pdfViewerScale', String(scale));
  }, [scale]);

  // Close on escape key and hide scroll
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      // Skip if focused on page input
      if (window.document.activeElement === pageInputRef.current) {
        return;
      }
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

  const zoomIn = useCallback(() => {
    setScale((prev) => Math.min(3, prev + 0.25));
  }, []);

  const zoomOut = useCallback(() => {
    setScale((prev) => Math.max(0.5, prev - 0.25));
  }, []);

  const resetZoom = useCallback(() => {
    setScale(1.0);
  }, []);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if focused on page input
      if (window.document.activeElement === pageInputRef.current) {
        return;
      }

      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        goToPrevPage();
      } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        goToNextPage();
      } else if (e.key === '+' || e.key === '=') {
        zoomIn();
      } else if (e.key === '-') {
        zoomOut();
      } else if (e.key === 'g') {
        // Press 'g' to focus page input
        pageInputRef.current?.focus();
        pageInputRef.current?.select();
        e.preventDefault();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [goToPrevPage, goToNextPage, zoomIn, zoomOut]);

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

  const handlePageInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value >= 1 && value <= numPages) {
      setPageNumber(value);
    }
  };

  const handlePageInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const value = parseInt((e.target as HTMLInputElement).value, 10);
      if (!isNaN(value) && value >= 1 && value <= numPages) {
        setPageNumber(value);
      }
      pageInputRef.current?.select();
    } else if (e.key === 'Escape') {
      pageInputRef.current?.blur();
    }
  };

  // Build file object with auth headers - memoized to prevent unnecessary PDF reloads
  const fileOptions = useMemo(
    () => ({
      url: pdfUrl,
      httpHeaders: {
        Authorization: `Bearer ${token}`,
      },
    }),
    [pdfUrl, token]
  );

  // Reset page rendered state when page or scale changes
  useEffect(() => {
    setPageRendered(false);
    setHighlights([]);
    setCurrentHighlightIndex(0);
  }, [pageNumber, scale]);

  // Scroll to a highlight element
  const scrollToHighlight = useCallback((element: HTMLElement) => {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, []);

  // Function to apply highlights to the text layer
  const applyHighlights = useCallback(() => {
    if (!searchQuery?.trim()) return;

    // Find the text layer container
    const textLayer = window.document.querySelector('.react-pdf__Page__textContent');
    if (!textLayer) return;

    // Clear previous highlights
    const existingHighlights = textLayer.querySelectorAll('.pdf-search-highlight');
    existingHighlights.forEach((el) => {
      const parent = el.parentNode;
      if (parent) {
        parent.replaceChild(window.document.createTextNode(el.textContent || ''), el);
        parent.normalize();
      }
    });

    const query = searchQuery.toLowerCase().trim();
    const newHighlights: HighlightMatch[] = [];
    let matchIndex = 0;

    // Get all text spans in the text layer
    const textSpans = textLayer.querySelectorAll('span');

    textSpans.forEach((span) => {
      const text = span.textContent || '';
      const lowerText = text.toLowerCase();
      let lastIndex = 0;
      let searchIndex = lowerText.indexOf(query);

      if (searchIndex === -1) return;

      // Build new content with highlights
      const fragment = window.document.createDocumentFragment();

      while (searchIndex !== -1) {
        // Add text before match
        if (searchIndex > lastIndex) {
          fragment.appendChild(
            window.document.createTextNode(text.slice(lastIndex, searchIndex))
          );
        }

        // Add highlighted match
        const highlightSpan = window.document.createElement('mark');
        highlightSpan.className = 'pdf-search-highlight';
        highlightSpan.textContent = text.slice(searchIndex, searchIndex + query.length);
        highlightSpan.dataset.matchIndex = String(matchIndex);
        fragment.appendChild(highlightSpan);

        newHighlights.push({ element: highlightSpan, index: matchIndex });
        matchIndex++;

        lastIndex = searchIndex + query.length;
        searchIndex = lowerText.indexOf(query, lastIndex);
      }

      // Add remaining text
      if (lastIndex < text.length) {
        fragment.appendChild(window.document.createTextNode(text.slice(lastIndex)));
      }

      // Replace span content
      span.textContent = '';
      span.appendChild(fragment);
    });

    setHighlights(newHighlights);

    // Scroll to first match
    if (newHighlights.length > 0) {
      setCurrentHighlightIndex(0);
      scrollToHighlight(newHighlights[0].element);
    }
  }, [searchQuery, scrollToHighlight]);

  // Highlight search query in text layer after page renders
  useEffect(() => {
    if (!pageRendered || !searchQuery?.trim()) {
      return;
    }

    // Small delay to ensure text layer is fully rendered after scale change
    const timeoutId = setTimeout(() => {
      applyHighlights();
    }, 50);

    return () => clearTimeout(timeoutId);
  }, [pageRendered, searchQuery, applyHighlights]);

  // Update active highlight styling
  useEffect(() => {
    highlights.forEach((h, i) => {
      if (i === currentHighlightIndex) {
        h.element.classList.add('pdf-search-highlight-active');
      } else {
        h.element.classList.remove('pdf-search-highlight-active');
      }
    });
  }, [currentHighlightIndex, highlights]);

  const goToNextHighlight = useCallback(() => {
    // If we have highlights on current page and not at the last one, go to next
    if (highlights.length > 0 && currentHighlightIndex < highlights.length - 1) {
      const nextIndex = currentHighlightIndex + 1;
      setCurrentHighlightIndex(nextIndex);
      scrollToHighlight(highlights[nextIndex].element);
      return;
    }

    // At last highlight on page (or no highlights), try to go to next page with matches
    if (matchingPages.length > 0) {
      const nextPage = matchingPages.find((p) => p > pageNumber);
      if (nextPage) {
        setPageNumber(nextPage);
        return;
      }
      // Wrap around to first matching page if at the end
      if (matchingPages[0] < pageNumber || matchingPages[0] === pageNumber) {
        const firstPage = matchingPages[0];
        if (firstPage !== pageNumber) {
          setPageNumber(firstPage);
        } else if (highlights.length > 0) {
          // Same page, wrap to first highlight
          setCurrentHighlightIndex(0);
          scrollToHighlight(highlights[0].element);
        }
      }
    }
  }, [highlights, currentHighlightIndex, pageNumber, matchingPages, scrollToHighlight]);

  const goToPrevHighlight = useCallback(() => {
    // If we have highlights on current page and not at the first one, go to previous
    if (highlights.length > 0 && currentHighlightIndex > 0) {
      const prevIndex = currentHighlightIndex - 1;
      setCurrentHighlightIndex(prevIndex);
      scrollToHighlight(highlights[prevIndex].element);
      return;
    }

    // At first highlight on page (or no highlights), try to go to previous page with matches
    if (matchingPages.length > 0) {
      const prevPage = [...matchingPages].reverse().find((p) => p < pageNumber);
      if (prevPage) {
        setPageNumber(prevPage);
        return;
      }
      // Wrap around to last matching page if at the beginning
      const lastPage = matchingPages[matchingPages.length - 1];
      if (lastPage > pageNumber || lastPage === pageNumber) {
        if (lastPage !== pageNumber) {
          setPageNumber(lastPage);
        } else if (highlights.length > 0) {
          // Same page, wrap to last highlight
          setCurrentHighlightIndex(highlights.length - 1);
          scrollToHighlight(highlights[highlights.length - 1].element);
        }
      }
    }
  }, [highlights, currentHighlightIndex, pageNumber, matchingPages, scrollToHighlight]);

  const onPageRenderSuccess = useCallback(() => {
    setPageRendered(true);
  }, []);

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
              title="축소 (-)"
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
              title="확대 (+)"
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

          {/* Search navigation - only show when there's a search query with highlights */}
          {searchQuery && highlights.length > 0 && (
            <div className="flex items-center gap-1 border-l border-gray-700 pl-4 mr-4">
              <button
                onClick={goToPrevHighlight}
                className="p-1.5 text-gray-300 hover:text-white hover:bg-gray-700 rounded transition-colors"
                title="이전 결과"
              >
                <ChevronLeftIcon className="h-4 w-4" />
              </button>
              <span className="text-sm text-yellow-400 px-2">
                {currentHighlightIndex + 1} / {highlights.length}
              </span>
              <button
                onClick={goToNextHighlight}
                className="p-1.5 text-gray-300 hover:text-white hover:bg-gray-700 rounded transition-colors"
                title="다음 결과"
              >
                <ChevronRightIcon className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Page navigation */}
          <div className="flex items-center gap-2 mr-4">
            <button
              onClick={goToPrevPage}
              disabled={pageNumber <= 1}
              className="p-2 rounded-lg text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="이전 페이지 (←)"
            >
              <ChevronLeftIcon className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-1 text-gray-300">
              <input
                ref={pageInputRef}
                type="number"
                min={1}
                max={numPages}
                value={pageNumber}
                onChange={handlePageInputChange}
                onKeyDown={handlePageInputKeyDown}
                className="w-14 px-2 py-1 text-center bg-gray-700 border border-gray-600 rounded text-white text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                title="페이지 번호 입력 (단축키: G)"
              />
              <span className="text-sm">/ {numPages}</span>
            </div>
            <button
              onClick={goToNextPage}
              disabled={pageNumber >= numPages}
              className="p-2 rounded-lg text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="다음 페이지 (→)"
            >
              <ChevronRightIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Close button */}
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-300 hover:bg-gray-700 transition-colors"
            title="닫기 (Esc)"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-auto bg-gray-700 flex items-start justify-center p-4">
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
            options={cMapOptions}
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
                renderTextLayer={true}
                renderAnnotationLayer={true}
                onRenderSuccess={onPageRenderSuccess}
              />
            )}
          </Document>
        )}
      </div>

      {/* Page quick navigation slider */}
      {numPages > 1 && (
        <div className="bg-gray-800 px-4 py-2">
          <input
            type="range"
            min={1}
            max={numPages}
            value={pageNumber}
            onChange={(e) => setPageNumber(Number(e.target.value))}
            className="w-full"
          />
        </div>
      )}
    </div>
  );
}
