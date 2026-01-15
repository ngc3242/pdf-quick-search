import { XMarkIcon } from '@heroicons/react/24/outline';
import type { TypoCheckProgress } from '@/types';

interface ProgressIndicatorProps {
  progress: TypoCheckProgress;
  onCancel: () => void;
  statusMessage?: string;
}

export const ProgressIndicator = ({
  progress,
  onCancel,
  statusMessage = '맞춤법 검사 중...',
}: ProgressIndicatorProps) => {
  const { current_chunk, total_chunks, percentage } = progress;

  return (
    <div data-testid="progress-indicator" className="w-full space-y-3">
      {/* Status and cancel button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-gray-700">{statusMessage}</span>
        </div>
        <button
          onClick={onCancel}
          className="flex items-center gap-1 px-2 py-1 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
          aria-label="취소"
        >
          <XMarkIcon className="w-4 h-4" />
          <span>취소</span>
        </button>
      </div>

      {/* Progress bar */}
      <div className="space-y-1">
        <div
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percentage}
          aria-label="맞춤법 검사 진행률"
          className="w-full h-2 bg-gray-200 rounded-full overflow-hidden"
        >
          <div
            data-testid="progress-fill"
            className="h-full bg-blue-500 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${percentage}%` }}
          />
        </div>

        {/* Progress text */}
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>
            청크 {current_chunk} / {total_chunks}
          </span>
          <span className="font-medium text-gray-700">{percentage}%</span>
        </div>
      </div>
    </div>
  );
};
