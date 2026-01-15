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
  const [copied, setCopied] = useState(false);

  const hasIssues = result.issues.length > 0;

  const handleCopy = async () => {
    try {
      // Copy only the corrected text without any numbers
      await navigator.clipboard.writeText(result.corrected_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy text:', error);
    }
  };

  // Build ordered issues list (by appearance in text) for consistent numbering
  const getOrderedIssues = (): { issue: TypoIssue; originalIndex: number }[] => {
    const orderedIssues: { issue: TypoIssue; originalIndex: number; position: number }[] = [];

    result.issues.forEach((issue, idx) => {
      const pos = result.corrected_text.indexOf(issue.corrected);
      if (pos !== -1) {
        orderedIssues.push({ issue, originalIndex: idx, position: pos });
      } else {
        // If not found in text, add at the end
        orderedIssues.push({ issue, originalIndex: idx, position: Infinity });
      }
    });

    // Sort by position in text
    orderedIssues.sort((a, b) => a.position - b.position);

    return orderedIssues.map(({ issue, originalIndex }) => ({ issue, originalIndex }));
  };

  const orderedIssues = hasIssues ? getOrderedIssues() : [];

  const renderHighlightedText = () => {
    if (!hasIssues) {
      return <p className="whitespace-pre-wrap">{result.corrected_text}</p>;
    }

    // Build highlighted text by finding each correction in corrected_text
    // This works for both live results and history (where original_text is empty)
    const parts: React.ReactNode[] = [];
    let searchStartIndex = 0;
    let correctionNumber = 0;

    // Process issues in order they appear in the text
    const processedIndices = new Set<number>();

    while (processedIndices.size < result.issues.length) {
      let earliestIndex = Infinity;
      let earliestIssue: TypoIssue | null = null;
      let earliestIssueIdx = -1;

      // Find the next correction that appears earliest in remaining text
      result.issues.forEach((issue, idx) => {
        if (processedIndices.has(idx)) return;

        const foundIndex = result.corrected_text.indexOf(issue.corrected, searchStartIndex);
        if (foundIndex !== -1 && foundIndex < earliestIndex) {
          earliestIndex = foundIndex;
          earliestIssue = issue;
          earliestIssueIdx = idx;
        }
      });

      if (!earliestIssue || earliestIndex === Infinity) {
        // No more corrections found, add remaining text
        break;
      }

      // Capture for TypeScript type narrowing
      const issue: TypoIssue = earliestIssue;
      correctionNumber++;

      processedIndices.add(earliestIssueIdx);

      // Add text before this correction
      if (earliestIndex > searchStartIndex) {
        const beforeText = result.corrected_text.slice(searchStartIndex, earliestIndex);
        parts.push(<span key={`text-${parts.length}`}>{beforeText}</span>);
      }

      // Add the correction with proofreading style, number badge, and tooltip
      parts.push(
        <span
          key={`correction-${parts.length}`}
          data-testid="highlight-correction"
          className="group relative inline-flex items-baseline gap-1 bg-amber-50 border-b-2 border-amber-400 px-0.5 rounded cursor-help"
        >
          {/* Number badge */}
          <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-blue-500 rounded-full flex-shrink-0">
            {correctionNumber}
          </span>
          <span className="text-red-500 text-sm line-through decoration-red-500">
            {issue.original}
          </span>
          <span className="text-green-700 font-medium">{issue.corrected}</span>
          {/* Tooltip */}
          <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-50 shadow-lg">
            {issue.explanation}
            <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
          </span>
        </span>
      );

      searchStartIndex = earliestIndex + issue.corrected.length;
    }

    // Add any remaining text after the last correction
    if (searchStartIndex < result.corrected_text.length) {
      parts.push(
        <span key={`text-end`}>{result.corrected_text.slice(searchStartIndex)}</span>
      );
    }

    return <p className="whitespace-pre-wrap leading-relaxed">{parts}</p>;
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

      {/* Result content */}
      <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 min-h-[200px]">
        {!hasIssues ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <CheckCircleIcon className="w-12 h-12 text-green-500 mb-3" />
            <p className="text-lg font-medium text-gray-900">오류가 없습니다!</p>
            <p className="text-sm text-gray-500 mt-1">입력하신 텍스트에 수정할 내용이 없습니다.</p>
          </div>
        ) : (
          renderHighlightedText()
        )}
      </div>

      {/* Issue list */}
      {hasIssues && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-700">수정 내역</h3>
          <div className="space-y-2">
            {orderedIssues.map(({ issue }, index) => (
              <div
                key={index}
                className="p-3 bg-white rounded-lg border border-gray-200 flex items-start gap-3"
              >
                {/* Number badge matching the text above */}
                <span className="inline-flex items-center justify-center w-6 h-6 text-xs font-bold text-white bg-blue-500 rounded-full flex-shrink-0">
                  {index + 1}
                </span>
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
