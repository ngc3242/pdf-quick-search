import {
  DocumentIcon,
  TrashIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { StatusBadge } from '@/components/common';
import type { Document } from '@/types';

interface DocumentCardProps {
  document: Document;
  onView: (doc: Document) => void;
  onDelete: (doc: Document) => void;
}

function formatFileSize(bytes: number | null): string {
  if (!bytes) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function DocumentCard({ document, onView, onDelete }: DocumentCardProps) {
  const canView = document.extraction_status === 'completed';

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-red-50 rounded-lg flex items-center justify-center">
            <DocumentIcon className="h-6 w-6 text-red-600" />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-sm font-medium text-gray-900 truncate">
              {document.original_filename}
            </h3>
            <StatusBadge status={document.extraction_status} />
          </div>

          <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
            <span>{formatFileSize(document.file_size_bytes)}</span>
            {document.page_count && <span>{document.page_count}p</span>}
            <span>{formatDate(document.uploaded_at)}</span>
          </div>

          {document.extraction_error && (
            <p className="mt-2 text-xs text-red-600 line-clamp-2">
              {document.extraction_error}
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex-shrink-0 flex items-center gap-1">
          <button
            onClick={() => onView(document)}
            disabled={!canView}
            className={`
              p-2 rounded-lg transition-colors
              ${canView
                ? 'text-gray-600 hover:bg-gray-100 hover:text-blue-600'
                : 'text-gray-300 cursor-not-allowed'
              }
            `}
            title={canView ? '보기' : '처리 완료 후 볼 수 있습니다'}
          >
            <EyeIcon className="h-5 w-5" />
          </button>
          <button
            onClick={() => onDelete(document)}
            className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 hover:text-red-600 transition-colors"
            title="삭제"
          >
            <TrashIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
