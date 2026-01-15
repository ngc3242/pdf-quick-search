import { useEffect, useState } from 'react';
import { XMarkIcon, DocumentMagnifyingGlassIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { useTypoCheckerStore } from '@/store';
import {
  TextInput,
  ProviderSelector,
  ResultDisplay,
  ReportDownload,
  ProgressIndicator,
} from '@/components/typo';
import { typoApi } from '@/api';
import type { ProviderAvailability } from '@/types';

export const TypoCheckerPage = () => {
  const {
    text,
    result,
    isLoading,
    error,
    selectedProvider,
    progress,
    setText,
    setProvider,
    checkTypo,
    cancelCheck,
    reset,
    clearError,
  } = useTypoCheckerStore();

  const [providerAvailability, setProviderAvailability] = useState<ProviderAvailability>({
    claude: true,
    openai: true,
    gemini: true,
  });

  useEffect(() => {
    // Fetch provider availability on mount
    const fetchAvailability = async () => {
      try {
        const availability = await typoApi.getProviderAvailability();
        setProviderAvailability(availability);
      } catch (err) {
        // Default to all available if API fails
        console.error('Failed to fetch provider availability:', err);
      }
    };

    fetchAvailability();
  }, []);

  const handleCheck = () => {
    checkTypo();
  };

  const handleReset = () => {
    reset();
  };

  const canCheck = text.trim().length > 0 && !isLoading;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <DocumentMagnifyingGlassIcon className="w-8 h-8 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">맞춤법 검사</h1>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="space-y-6">
          {/* Error message */}
          {error && (
            <div className="flex items-center justify-between p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700">{error}</p>
              <button
                onClick={clearError}
                className="p-1 text-red-500 hover:text-red-700 hover:bg-red-100 rounded transition-colors"
                aria-label="닫기"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
          )}

          {/* Input section */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="space-y-4">
              {/* Provider selector */}
              <div className="max-w-xs">
                <ProviderSelector
                  value={selectedProvider}
                  onChange={setProvider}
                  availability={providerAvailability}
                  disabled={isLoading}
                  label="AI 모델 선택"
                />
              </div>

              {/* Text input */}
              <TextInput
                value={text}
                onChange={setText}
                disabled={isLoading}
                label="검사할 텍스트"
                placeholder="맞춤법을 검사할 텍스트를 입력하세요... (최대 100,000자)"
              />

              {/* Action buttons */}
              <div className="flex items-center gap-3">
                <button
                  onClick={handleCheck}
                  disabled={!canCheck}
                  className={`
                    flex items-center gap-2 px-6 py-2.5 text-sm font-medium rounded-lg
                    bg-blue-600 text-white
                    hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                    disabled:opacity-50 disabled:cursor-not-allowed
                    transition-colors
                  `}
                >
                  {isLoading ? (
                    <>
                      <ArrowPathIcon className="w-4 h-4 animate-spin" />
                      검사 중...
                    </>
                  ) : (
                    <>
                      <DocumentMagnifyingGlassIcon className="w-4 h-4" />
                      검사하기
                    </>
                  )}
                </button>

                {(text || result) && (
                  <button
                    onClick={handleReset}
                    disabled={isLoading}
                    className={`
                      flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg
                      border border-gray-300 text-gray-700 bg-white
                      hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2
                      disabled:opacity-50 disabled:cursor-not-allowed
                      transition-colors
                    `}
                  >
                    <ArrowPathIcon className="w-4 h-4" />
                    새로 검사
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Progress indicator */}
          {isLoading && progress && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <ProgressIndicator
                progress={progress}
                onCancel={cancelCheck}
                statusMessage="텍스트를 분석하고 있습니다..."
              />
            </div>
          )}

          {/* Result section */}
          {result && !isLoading && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-6">
              <ResultDisplay result={result} />
              <div className="pt-4 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-700 mb-3">결과 다운로드</h3>
                <ReportDownload result={result} />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
