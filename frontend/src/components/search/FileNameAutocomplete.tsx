/**
 * File name autocomplete component
 * Adapted from SARA - SPEC-SEARCH-001: REQ-E001, REQ-E002
 *
 * Features:
 * - 150ms debounce before filtering
 * - Case-insensitive substring match
 * - Dropdown list with filtered results
 * - Keyboard navigation: Arrow Up/Down, Enter to select, Escape to close
 * - Click to select file
 * - Auto-opens PDF viewer with page input focused
 */
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import type { Document } from '@/types';

interface FileNameAutocompleteProps {
  documents: Document[];
  onSelect: (document: Document) => void;
}

const DEBOUNCE_MS = 150;
const MAX_RESULTS = 10;

/**
 * Get status icon for document
 */
function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'completed':
      return (
        <span className="material-symbols-outlined text-[16px] text-green-500">
          check_circle
        </span>
      );
    case 'processing':
      return (
        <span className="material-symbols-outlined text-[16px] text-blue-500 animate-pulse">
          progress_activity
        </span>
      );
    case 'failed':
      return (
        <span className="material-symbols-outlined text-[16px] text-red-500">
          error
        </span>
      );
    default:
      return (
        <span className="material-symbols-outlined text-[16px] text-yellow-500">
          schedule
        </span>
      );
  }
}

/**
 * File name autocomplete with dropdown and keyboard navigation
 */
export function FileNameAutocomplete({ documents, onSelect }: FileNameAutocompleteProps) {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isComposing, setIsComposing] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Filter documents based on debounced query
  // Uses Unicode NFC normalization for Korean/CJK text compatibility
  const filteredDocuments = useMemo(() => {
    if (!debouncedQuery.trim()) {
      return [];
    }
    // Normalize both query and filenames to NFC for consistent Korean text matching
    const normalizedQuery = debouncedQuery.normalize('NFC').toLowerCase();
    return documents
      .filter((doc) => doc.original_filename.normalize('NFC').toLowerCase().includes(normalizedQuery))
      .slice(0, MAX_RESULTS);
  }, [documents, debouncedQuery]);

  // Debounce query changes (skip during IME composition for Korean/CJK input)
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // Don't update debounced query while composing (Korean/CJK input)
    if (isComposing) {
      return;
    }

    debounceRef.current = setTimeout(() => {
      setDebouncedQuery(query);
      if (query.trim()) {
        setIsOpen(true);
        // Reset selected index when query changes (results will change)
        setSelectedIndex(0);
      }
    }, DEBOUNCE_MS);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query, isComposing]);

  // Scroll selected item into view
  useEffect(() => {
    if (listRef.current && isOpen) {
      const selectedItem = listRef.current.children[selectedIndex] as HTMLElement;
      if (selectedItem) {
        selectedItem.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [selectedIndex, isOpen]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    if (!e.target.value.trim()) {
      setIsOpen(false);
    }
  }, []);

  const handleSelect = useCallback(
    (document: Document) => {
      setQuery('');
      setDebouncedQuery('');
      setIsOpen(false);
      onSelect(document);
    },
    [onSelect]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (!isOpen || filteredDocuments.length === 0) {
        if (e.key === 'Escape') {
          setQuery('');
          setIsOpen(false);
        }
        return;
      }

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev < filteredDocuments.length - 1 ? prev + 1 : prev
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredDocuments[selectedIndex]) {
            handleSelect(filteredDocuments[selectedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          setIsOpen(false);
          break;
        case 'Tab':
          setIsOpen(false);
          break;
      }
    },
    [isOpen, filteredDocuments, selectedIndex, handleSelect]
  );

  const handleClear = useCallback(() => {
    setQuery('');
    setDebouncedQuery('');
    setIsOpen(false);
    inputRef.current?.focus();
  }, []);

  const handleBlur = useCallback(() => {
    // Delay closing to allow click on dropdown items
    setTimeout(() => {
      if (!listRef.current?.contains(document.activeElement)) {
        setIsOpen(false);
      }
    }, 150);
  }, []);

  const handleFocus = useCallback(() => {
    if (debouncedQuery.trim() && filteredDocuments.length > 0) {
      setIsOpen(true);
    }
  }, [debouncedQuery, filteredDocuments.length]);

  // IME composition handlers for Korean/CJK input
  const handleCompositionStart = useCallback(() => {
    setIsComposing(true);
  }, []);

  const handleCompositionEnd = useCallback((e: React.CompositionEvent<HTMLInputElement>) => {
    setIsComposing(false);
    const finalValue = e.currentTarget.value;
    setQuery(finalValue);
    // Directly update debouncedQuery to bypass race condition
    setTimeout(() => {
      setDebouncedQuery(finalValue);
      if (finalValue.trim()) {
        setIsOpen(true);
        setSelectedIndex(0);
      }
    }, 50);
  }, []);

  return (
    <div className="relative">
      {/* Search Input */}
      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
          <span className="material-symbols-outlined text-[20px] text-text-secondary">
            description
          </span>
        </div>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          onFocus={handleFocus}
          onCompositionStart={handleCompositionStart}
          onCompositionEnd={handleCompositionEnd}
          placeholder="파일명으로 검색..."
          className="block w-full rounded-lg border border-[#dbe0e6] py-2.5 pl-10 pr-10 text-sm
            text-text-primary placeholder-text-secondary
            focus:border-primary focus:ring-2 focus:ring-primary/50 focus:outline-none"
          autoComplete="off"
          role="combobox"
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          aria-controls="file-autocomplete-list"
        />
        {query && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute inset-y-0 right-0 flex items-center pr-3 text-text-secondary hover:text-text-primary transition-colors"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        )}
      </div>

      {/* Dropdown Results */}
      {isOpen && filteredDocuments.length > 0 && (
        <ul
          ref={listRef}
          id="file-autocomplete-list"
          role="listbox"
          className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-[#dbe0e6] bg-white shadow-lg"
        >
          {filteredDocuments.map((doc, index) => (
            <li
              key={doc.id}
              role="option"
              aria-selected={index === selectedIndex}
              onClick={() => handleSelect(doc)}
              onMouseEnter={() => setSelectedIndex(index)}
              className={`flex items-center gap-3 px-3 py-2 cursor-pointer
                ${index === selectedIndex ? 'bg-primary/10' : 'hover:bg-gray-50'}
                ${doc.extraction_status !== 'completed' ? 'opacity-60' : ''}`}
            >
              <div className="size-8 rounded-lg bg-red-50 flex items-center justify-center flex-shrink-0">
                <span className="material-symbols-outlined text-red-500">picture_as_pdf</span>
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-text-primary truncate">
                  {doc.original_filename}
                </p>
                <p className="text-xs text-text-secondary">
                  {doc.page_count ? `${doc.page_count} pages` : 'Page count unknown'}
                </p>
              </div>
              <StatusIcon status={doc.extraction_status} />
            </li>
          ))}
        </ul>
      )}

      {/* No Results Message */}
      {isOpen && debouncedQuery.trim() && filteredDocuments.length === 0 && (
        <div className="absolute z-50 mt-1 w-full rounded-lg border border-[#dbe0e6] bg-white px-4 py-3 shadow-lg">
          <p className="text-sm text-text-secondary">검색 결과가 없습니다</p>
        </div>
      )}

      {/* Helper Text */}
      {!isOpen && (
        <p className="mt-1 text-xs text-text-secondary pl-1">
          파일명을 입력하고 Enter로 선택하세요. 화살표 키로 탐색 가능합니다.
        </p>
      )}
    </div>
  );
}

export default FileNameAutocomplete;
