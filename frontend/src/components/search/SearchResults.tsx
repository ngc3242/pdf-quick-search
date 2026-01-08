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
      <div className="flex flex-col items-center justify-center py-16">
        <div className="size-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
          <span className="material-symbols-outlined text-4xl text-primary animate-pulse">search</span>
        </div>
        <p className="text-text-secondary text-base">Searching documents...</p>
      </div>
    );
  }

  if (!query) {
    return null;
  }

  if (results.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="size-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
          <span className="material-symbols-outlined text-4xl text-gray-400">search_off</span>
        </div>
        <p className="text-text-primary text-lg font-medium">No results found</p>
        <p className="text-text-secondary text-sm mt-1">
          Try different keywords or check your spelling
        </p>
      </div>
    );
  }

  // Group results by document
  const groupedResults = results.reduce((acc, result) => {
    const docId = result.document.id;
    if (!acc[docId]) {
      acc[docId] = {
        document: result.document,
        snippets: [],
      };
    }
    acc[docId].snippets.push({
      page_number: result.page_number,
      snippet: result.snippet,
    });
    return acc;
  }, {} as Record<number, { document: Document; snippets: { page_number: number; snippet: string }[] }>);

  return (
    <div className="flex flex-col gap-6">
      {/* Results Meta */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#e5e7eb] pb-4">
        <div className="flex gap-2 flex-wrap">
          <button className="flex h-8 items-center gap-2 rounded-lg bg-white border border-[#dbe0e6] px-3 hover:border-primary/50 hover:text-primary transition-colors group shadow-sm">
            <span className="text-text-secondary group-hover:text-primary text-sm font-medium">Relevance</span>
            <span className="material-symbols-outlined text-text-secondary text-sm group-hover:text-primary">
              arrow_drop_down
            </span>
          </button>
        </div>
        <p className="text-text-secondary text-sm">
          Found <span className="font-medium text-text-primary">{total}</span> results for "{query}"
        </p>
      </div>

      {/* Results List */}
      <div className="flex flex-col gap-4">
        {Object.values(groupedResults).map(({ document, snippets }) => (
          <article
            key={document.id}
            className="flex flex-col bg-white rounded-xl p-5 border border-[#e5e7eb] shadow-sm hover:shadow-md transition-all"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                {/* Document Header */}
                <div className="flex items-center gap-2 mb-2">
                  <span className="material-symbols-outlined text-red-500 text-[24px]">picture_as_pdf</span>
                  <button
                    onClick={() => onDocumentClick(document, snippets[0]?.page_number || 1)}
                    className="text-lg font-bold text-primary hover:underline decoration-2 underline-offset-2"
                  >
                    {document.original_filename}
                  </button>
                  <span className="text-xs text-text-secondary font-medium">
                    {document.file_size_bytes && `• ${formatFileSize(document.file_size_bytes)}`} {document.page_count && `• ${document.page_count} pages`}
                  </span>
                </div>

                {/* Snippets */}
                {snippets.slice(0, 3).map((snippet, index) => (
                  <div key={index} className={index > 0 ? 'mt-4' : ''}>
                    <p className="text-text-secondary text-sm leading-7 mb-2">
                      <HighlightedSnippet text={snippet.snippet} query={query} />
                    </p>
                    <div className="flex items-center gap-3">
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-semibold bg-[#f9fafb] text-text-secondary border border-[#e5e7eb]">
                        Page {snippet.page_number}
                      </span>
                      <button
                        onClick={() => onDocumentClick(document, snippet.page_number)}
                        className="text-primary text-sm font-semibold hover:text-blue-700 flex items-center gap-1 transition-colors px-2 py-1 rounded hover:bg-blue-50"
                      >
                        View in context{' '}
                        <span className="material-symbols-outlined text-base">open_in_new</span>
                      </button>
                    </div>
                  </div>
                ))}

                {/* More Results Link */}
                {snippets.length > 3 && (
                  <div className="pl-4 border-l-2 border-[#e5e7eb] mt-4 pt-2">
                    <button className="text-sm text-text-secondary hover:text-primary font-medium flex items-center gap-1 transition-colors group">
                      <span className="material-symbols-outlined text-xl group-hover:translate-y-0.5 transition-transform">
                        expand_more
                      </span>
                      More results ({snippets.length - 3} more)
                    </button>
                  </div>
                )}
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
