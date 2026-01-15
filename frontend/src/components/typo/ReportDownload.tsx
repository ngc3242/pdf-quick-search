import { useState } from 'react';
import {
  DocumentArrowDownIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import type { TypoCheckResult } from '@/types';
import { typoApi } from '@/api';

interface ReportDownloadProps {
  result: TypoCheckResult;
  disabled?: boolean;
}

type DownloadFormat = 'html' | 'pdf';

export const ReportDownload = ({ result, disabled = false }: ReportDownloadProps) => {
  const [isDownloading, setIsDownloading] = useState<DownloadFormat | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async (format: DownloadFormat) => {
    setIsDownloading(format);
    setError(null);

    try {
      const blob = await typoApi.downloadReport(result, format);

      // Create download link
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `typo-check-report.${format}`;
      link.style.display = 'none';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Cleanup
      URL.revokeObjectURL(url);
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : '다운로드에 실패했습니다';
      setError(errorMessage);
    } finally {
      setIsDownloading(null);
    }
  };

  const isLoading = isDownloading !== null;

  return (
    <div data-testid="report-download" className="space-y-3">
      <div className="flex items-center gap-3">
        <button
          onClick={() => handleDownload('html')}
          disabled={disabled || isLoading}
          className={`
            flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg
            border border-gray-300 bg-white
            hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors
          `}
        >
          {isDownloading === 'html' ? (
            <ArrowPathIcon className="w-4 h-4 animate-spin" />
          ) : (
            <DocumentArrowDownIcon className="w-4 h-4" />
          )}
          HTML 다운로드
        </button>

        <button
          onClick={() => handleDownload('pdf')}
          disabled={disabled || isLoading}
          className={`
            flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg
            border border-gray-300 bg-white
            hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors
          `}
        >
          {isDownloading === 'pdf' ? (
            <ArrowPathIcon className="w-4 h-4 animate-spin" />
          ) : (
            <DocumentArrowDownIcon className="w-4 h-4" />
          )}
          PDF 다운로드
        </button>
      </div>

      {error && (
        <p className="text-sm text-red-600">
          다운로드 오류: {error}
        </p>
      )}
    </div>
  );
};
