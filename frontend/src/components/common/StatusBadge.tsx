import type { ExtractionStatus } from '@/types';

interface StatusBadgeProps {
  status: ExtractionStatus;
}

const statusConfig: Record<
  ExtractionStatus,
  { label: string; className: string }
> = {
  pending: {
    label: '대기중',
    className: 'bg-gray-100 text-gray-700',
  },
  processing: {
    label: '처리중',
    className: 'bg-blue-100 text-blue-700',
  },
  completed: {
    label: '완료',
    className: 'bg-green-100 text-green-700',
  },
  failed: {
    label: '실패',
    className: 'bg-red-100 text-red-700',
  },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status];

  return (
    <span
      className={`
        inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
        ${config.className}
      `}
    >
      {status === 'processing' && (
        <svg
          className="animate-spin -ml-0.5 mr-1.5 h-3 w-3"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {config.label}
    </span>
  );
}
