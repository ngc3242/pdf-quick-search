import { TrashIcon, ClockIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import type { TypoHistoryItem } from '@/types';

interface HistoryPanelProps {
  history: TypoHistoryItem[];
  isLoading: boolean;
  error: string | null;
  selectedHistoryId: number | null;
  deletingId: number | null;
  onSelect: (id: number) => void;
  onDelete: (id: number) => void;
}

const PROVIDER_DISPLAY_NAMES: Record<string, string> = {
  claude: 'Claude',
  openai: 'OpenAI',
  gemini: 'Gemini',
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const truncateText = (text: string, maxLength: number = 50): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

export const HistoryPanel = ({
  history,
  isLoading,
  error,
  selectedHistoryId,
  deletingId,
  onSelect,
  onDelete,
}: HistoryPanelProps) => {
  const handleDelete = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    const confirmed = window.confirm('이 검사 기록을 삭제하시겠습니까?');
    if (confirmed) {
      onDelete(id);
    }
  };

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            data-testid="history-skeleton"
            className="bg-white border border-gray-200 rounded-lg p-4 animate-pulse"
          >
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-gray-200 rounded-lg flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="h-4 bg-gray-200 rounded w-2/3 mb-2" />
                <div className="h-3 bg-gray-200 rounded w-1/3 mb-2" />
                <div className="h-3 bg-gray-200 rounded w-1/2" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
        <ExclamationCircleIcon className="w-5 h-5 text-red-500 flex-shrink-0" />
        <p className="text-sm text-悪-700">{error}</p>
      </div>
    );
  }

  // Empty state
  if (history.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <ClockIcon className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-medium text-gray-900">검사 기록이 없습니다</h3>
        <p className="mt-1 text-sm text-gray-500">
          맞춤법 검사를 하면 기록이 여기에 표시됩니다.
        </p>
      </div>
    );
  }

  // History list
  return (
    <div className="space-y-2">
      {history.map((item) => {
        const isSelected = selectedHistoryId === item.id;
        const isDeleting = deletingId === item.id;

        return (
          <div
            key={item.id}
            data-testid="history-item"
            onClick={() => onSelect(item.id)}
            className={`
              relative cursor-pointer p-4 rounded-lg border transition-all
              ${isSelected
                ? 'bg-blue-50 border-blue-300 ring-1 ring-blue-300'
                : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm'
              }
            `}
          >
            <div className="flex items-start gap-3">
              {/* Provider badge */}
              <div className={`
                w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-bold
                ${item.provider === 'claude' ? 'bg-orange-100 text-orange-700' : ''}
                ${item.provider === 'openai' ? 'bg-green-100 text-green-700' : ''}
                ${item.provider === 'gemini' ? 'bg-blue-100 text-blue-700' : ''}
              `}>
                {PROVIDER_DISPLAY_NAMES[item.provider]?.charAt(0) || 'AI'}
              </div>

              <div className="flex-1 min-w-0">
                {/* Preview text */}
                <p
                  data-testid="history-preview"
                  className="text-sm text-gray-900 truncate mb-1"
                >
                  {truncateText(item.corrected_text, 60)}
                </p>

                {/* Meta info */}
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span>{PROVIDER_DISPLAY_NAMES[item.provider] || item.provider}</span>
                  <span className={`
                    px-1.5 py-0.5 rounded
                    ${item.issue_count > 0 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}
                  `}>
                    {item.issue_count}개 오류
                  </span>
                </div>

                {/* Date */}
                <p className="text-xs text-gray-400 mt-1">
                  {formatDate(item.created_at)}
                </p>
              </div>

              {/* Delete button */}
              <button
                data-testid="delete-button"
                onClick={(e) => handleDelete(e, item.id)}
                disabled={isDeleting}
                className={`
                  p-2 rounded-lg transition-colors flex-shrink-0
                  ${isDeleting
                    ? 'opacity-50 cursor-not-allowed'
                    : 'text-gray-400 hover:text-red-500 hover:bg-red-50'
                  }
                `}
                aria-label="삭제"
              >
                {isDeleting ? (
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                ) : (
                  <TrashIcon className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};
