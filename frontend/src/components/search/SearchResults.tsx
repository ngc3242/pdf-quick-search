import { DocumentIcon } from '@heroicons/react/24/outline';
import { HighlightedSnippet } from './HighlightedSnippet';
import type { SearchResult, Document } from '@/types';

interface SearchResultsProps {
  results: SearchResult[];
  total: number;
  query: string;
  isSearching: boolean;
  onDocumentClick: (doc: Document, pageNumber: number) => void;
}

export function SearchResults({
  results,
  total,
  query,
  isSearching,
  onDocumentClick,
}: SearchResultsProps) {
  if (isSearching) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4" />
        <p className="text-gray-600">검색 중...</p>
      </div>
    );
  }

  if (!query) {
    return null;
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg
            className="h-8 w-8 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <p className="text-gray-600">검색 결과가 없습니다</p>
        <p className="text-sm text-gray-500 mt-1">
          다른 검색어로 시도해 보세요
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600">
        "{query}" 검색 결과: <span className="font-medium">{total}건</span>
      </p>

      <div className="space-y-3">
        {results.map((result, index) => (
          <button
            key={`${result.document.id}-${result.page_number}-${index}`}
            onClick={() => onDocumentClick(result.document, result.page_number)}
            className="w-full text-left bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md hover:border-blue-300 transition-all"
          >
            <div className="flex items-start gap-3">
              {/* Icon */}
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center">
                  <DocumentIcon className="h-5 w-5 text-red-600" />
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-medium text-gray-900 truncate">
                    {result.document.original_filename}
                  </h3>
                  <span className="text-xs text-gray-500 flex-shrink-0">
                    페이지 {result.page_number}
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-600 line-clamp-2">
                  <HighlightedSnippet text={result.snippet} query={query} />
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
