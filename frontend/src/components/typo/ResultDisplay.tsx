import { useState } from 'react';
import {
  CheckCircleIcon,
  ClipboardDocumentIcon,
  ClipboardDocumentCheckIcon,
} from '@heroicons/react/24/outline';
import type { TypoCheckResult, TypoIssue } from '@/types';

interface ResultDisplayProps {
  result: TypoCheckResult;
}

type ViewMode = 'corrected' | 'diff';

const ISSUE_TYPE_LABELS: Record<TypoIssue['type'], string> = {
  spelling: '맞춤법',
  grammar: '문법',
  punctuation: '구두점',
  style: '스타일',
};

const ISSUE_TYPE_COLORS: Record<TypoIssue['type'], string> = {
  spelling: 'bg-red-100 text-red-800',
  grammar: 'bg-yellow-100 text-yellow-800',
  punctuation: 'bg-blue-100 text-blue-800',
  style: 'bg-purple-100 text-purple-800',
};

const formatProcessingTime = (ms: number): string => {
  if (ms >= 1000) {
    return `${(ms / 1000).toFixed(1)}초`;
  }
  return `${ms}ms`;
};

const providerDisplayNames: Record<string, string> = {
  claude: 'Claude',
  openai: 'OpenAI',
  gemini: 'Gemini',
};

export const ResultDisplay = ({ result }: ResultDisplayProps) => {
  const [viewMode, setViewMode] = useState<ViewMode>('corrected');
  const [copied, setCopied] = useState(false);

  const hasIssues = result.issues.length > 0;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result.corrected_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy text:', error);
    }
  };

  const renderHighlightedText = () => {
    if (!hasIssues) {
      return <p className="whitespace-pre-wrap">{result.corrected_text}</p>;
    }

    // Sort issues by position to render in order
    const sortedIssues = [...result.issues].sort(
      (a, b) => a.position.start - b.position.start
    );

    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    sortedIssues.forEach((issue, idx) => {
      // Add text before the correction
      if (issue.position.start > lastIndex) {
        const beforeText = result.corrected_text.slice(lastIndex, issue.position.start);
        parts.push(<span key={`text-${idx}`}>{beforeText}</span>);
      }

      // Add the highlighted correction
      parts.push(
        <span
          key={`highlight-${idx}`}
          data-testid="highlight-correction"
          className="bg-green-100 text-green-800 px-1 rounded"
          title={`${issue.original} → ${issue.corrected}`}
        >
          {issue.corrected}
        </span>
      );

      lastIndex = issue.position.end;
    });

    // Add remaining text after last correction
    if (lastIndex < result.corrected_text.length) {
      parts.push(
        <span key="text-end">{result.corrected_text.slice(lastIndex)}</span>
      );
    }

    return <p className="whitespace-pre-wrap">{parts}</p>;
  };

  const renderDiffView = () => {
    return (
      <div className="space-y-4">
        <div>
          <h4 className="text-sm font-medium text-gray-500 mb-2">원본</h4>
          <p className="whitespace-pre-wrap p-3 bg-red-50 rounded-lg border border-red-100">
            {result.original_text}
          </p>
        </div>
        <div>
          <h4 className="text-sm font-medium text-gray-500 mb-2">수정됨</h4>
          <p className="whitespace-pre-wrap p-3 bg-green-50 rounded-lg border border-green-100">
            {result.corrected_text}
          </p>
        </div>
      </div>
    );
  };

  return (
    <div data-testid="result-display" className="w-full space-y-6">
      {/* Header with stats */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">
            발견된 오류: <strong className="text-gray-900">{result.issues.length}개</strong>
          </span>
          <span className="text-sm text-gray-600">
            처리 시간: <strong className="text-gray-900">{formatProcessingTime(result.processing_time_ms)}</strong>
          </span>
          <span className="text-sm text-gray-600">
            AI: <strong className="text-gray-900">{providerDisplayNames[result.provider] || result.provider}</strong>
          </span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          aria-label={copied ? '복사됨' : '복사'}
        >
          {copied ? (
            <>
              <ClipboardDocumentCheckIcon className="w-4 h-4 text-green-600" />
              <span className="text-green-600">복사됨</span>
            </>
          ) : (
            <>
              <ClipboardDocumentIcon className="w-4 h-4" />
              <span>복사</span>
            </>
          )}
        </button>
      </div>

      {/* View mode tabs */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setViewMode('corrected')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            viewMode === 'corrected'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          수정된 텍스트
        </button>
        <button
          onClick={() => setViewMode('diff')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            viewMode === 'diff'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          원문 비교
        </button>
      </div>

      {/* Result content */}
      <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 min-h-[200px]">
        {!hasIssues ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <CheckCircleIcon className="w-12 h-12 text-green-500 mb-3" />
            <p className="text-lg font-medium text-gray-900">오류가 없습니다!</p>
            <p className="text-sm text-gray-500 mt-1">입력하신 텍스트에 수정할 내용이 없습니다.</p>
          </div>
        ) : viewMode === 'corrected' ? (
          renderHighlightedText()
        ) : (
          renderDiffView()
        )}
      </div>

      {/* Issue list */}
      {hasIssues && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-700">수정 내역</h3>
          <div className="space-y-2">
            {result.issues.map((issue, index) => (
              <div
                key={index}
                className="p-3 bg-white rounded-lg border border-gray-200 flex items-start gap-3"
              >
                <span
                  className={`px-2 py-0.5 text-xs font-medium rounded ${ISSUE_TYPE_COLORS[issue.type]}`}
                >
                  {ISSUE_TYPE_LABELS[issue.type]}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm">
                    <span className="line-through text-red-600">{issue.original}</span>
                    <span className="mx-2 text-gray-400">→</span>
                    <span className="text-green-600 font-medium">{issue.corrected}</span>
                  </p>
                  <p className="text-xs text-gray-500 mt-1">{issue.explanation}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
