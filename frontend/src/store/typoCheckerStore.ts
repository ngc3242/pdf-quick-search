import { create } from 'zustand';
import type {
  TypoCheckResult,
  TypoProvider,
  TypoCheckProgress,
  TypoHistoryItem,
  TypoCheckJobPollResult,
} from '@/types';
import { typoApi } from '@/api';

const POLL_INTERVAL = 1500; // 1.5 seconds
const MAX_POLL_TIME = 10 * 60 * 1000; // 10 minutes

async function pollForCompletion(
  jobId: number,
  onProgress: (progress: TypoCheckProgress) => void
): Promise<TypoCheckJobPollResult> {
  const startTime = Date.now();
  let consecutiveErrors = 0;

  while (true) {
    try {
      const status = await typoApi.getJobStatus(jobId);
      consecutiveErrors = 0;

      if (status.progress) {
        onProgress(status.progress);
      }

      if (['completed', 'failed', 'cancelled'].includes(status.status)) {
        return status;
      }
    } catch {
      consecutiveErrors++;
      if (consecutiveErrors >= 5) {
        throw new Error('서버 연결에 실패했습니다');
      }
    }

    if (Date.now() - startTime > MAX_POLL_TIME) {
      throw new Error('맞춤법 검사 시간이 초과되었습니다');
    }

    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL));
  }
}

interface TypoCheckerState {
  text: string;
  result: TypoCheckResult | null;
  isLoading: boolean;
  error: string | null;
  selectedProvider: TypoProvider;
  progress: TypoCheckProgress | null;
  currentJobId: number | null;

  // History state (SPEC-HISTORY-001)
  history: TypoHistoryItem[];
  historyPage: number;
  historyPerPage: number;
  historyTotal: number;
  historyPages: number;
  isHistoryLoading: boolean;
  historyError: string | null;
  selectedHistoryId: number | null;
  deletingId: number | null;

  // Actions
  setText: (text: string) => void;
  setProvider: (provider: TypoProvider) => void;
  checkTypo: () => Promise<void>;
  setProgress: (progress: TypoCheckProgress) => void;
  cancelCheck: () => void;
  reset: () => void;
  clearError: () => void;

  // History actions (SPEC-HISTORY-001)
  loadHistory: (page?: number) => Promise<void>;
  selectHistory: (id: number) => void;
  deleteHistory: (id: number) => Promise<void>;
  clearHistorySelection: () => void;
}

const initialState = {
  text: '',
  result: null,
  isLoading: false,
  error: null,
  selectedProvider: 'gemini' as TypoProvider,
  progress: null,
  currentJobId: null as number | null,
  // History initial state (SPEC-HISTORY-001)
  history: [] as TypoHistoryItem[],
  historyPage: 1,
  historyPerPage: 20,
  historyTotal: 0,
  historyPages: 0,
  isHistoryLoading: false,
  historyError: null as string | null,
  selectedHistoryId: null as number | null,
  deletingId: null as number | null,
};

export const useTypoCheckerStore = create<TypoCheckerState>((set, get) => ({
  ...initialState,

  setText: (text: string) => {
    set({ text, error: null });
  },

  setProvider: (provider: TypoProvider) => {
    set({ selectedProvider: provider });
  },

  checkTypo: async () => {
    const { text, selectedProvider } = get();

    if (!text.trim()) {
      return;
    }

    set({
      isLoading: true,
      error: null,
      result: null,
      progress: null,
      currentJobId: null,
    });

    try {
      const response = await typoApi.checkTypo({
        text,
        provider: selectedProvider,
      });

      if (response.cached) {
        // Cache hit - done immediately
        set({ result: response.result, isLoading: false });
        return;
      }

      // Job created - start polling
      const jobId = response.job_id;
      set({ currentJobId: jobId });

      const pollResult = await pollForCompletion(jobId, (progress) => {
        set({ progress });
      });

      if (pollResult.status === 'completed' && pollResult.result) {
        const result: TypoCheckResult = {
          original_text: pollResult.result.original_text,
          corrected_text: pollResult.result.corrected_text,
          issues: pollResult.result.issues,
          provider: pollResult.result.provider,
          processing_time_ms: 0,
          chunk_count: pollResult.progress.total_chunks,
        };
        set({ result, isLoading: false, progress: null, currentJobId: null });
      } else if (pollResult.status === 'failed') {
        set({
          error: pollResult.error_message || '맞춤법 검사에 실패했습니다',
          isLoading: false,
          progress: null,
          currentJobId: null,
        });
      } else if (pollResult.status === 'cancelled') {
        set({ isLoading: false, progress: null, currentJobId: null });
      }
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : '맞춤법 검사 중 오류가 발생했습니다';
      set({
        error: errorMessage,
        isLoading: false,
        result: null,
        progress: null,
        currentJobId: null,
      });
    }
  },

  setProgress: (progress: TypoCheckProgress) => {
    set({ progress });
  },

  cancelCheck: () => {
    const { currentJobId } = get();
    if (currentJobId) {
      typoApi.cancelJob(currentJobId).catch(() => {});
    }
    set({ isLoading: false, progress: null, currentJobId: null });
  },

  reset: () => {
    set(initialState);
  },

  clearError: () => {
    set({ error: null });
  },

  // History actions (SPEC-HISTORY-001)
  loadHistory: async (page?: number) => {
    const { historyPerPage } = get();
    const targetPage = page ?? 1;

    set({ isHistoryLoading: true, historyError: null });

    try {
      const response = await typoApi.getHistory(targetPage, historyPerPage);
      set({
        history: response.history,
        historyPage: response.page,
        historyTotal: response.total,
        historyPages: response.pages,
        isHistoryLoading: false,
      });
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : '히스토리를 불러오는 중 오류가 발생했습니다';
      set({ historyError: errorMessage, isHistoryLoading: false });
    }
  },

  selectHistory: (id: number) => {
    const { history } = get();
    const historyItem = history.find((item) => item.id === id);

    if (historyItem) {
      // Convert TypoHistoryItem to TypoCheckResult format
      const result: TypoCheckResult = {
        original_text: historyItem.original_text,
        corrected_text: historyItem.corrected_text,
        issues: historyItem.issues,
        provider: historyItem.provider,
        processing_time_ms: 0, // Not available in history
        chunk_count: 0, // Not available in history
      };
      // Also restore the text input and provider selection
      set({
        selectedHistoryId: id,
        result,
        text: historyItem.original_text,
        selectedProvider: historyItem.provider,
      });
    } else {
      set({ selectedHistoryId: id });
    }
  },

  deleteHistory: async (id: number) => {
    set({ deletingId: id, historyError: null });

    try {
      await typoApi.deleteHistoryItem(id);
      const { history, historyTotal, selectedHistoryId } = get();

      // Remove item from history
      const updatedHistory = history.filter((item) => item.id !== id);

      // Clear selection if deleted item was selected
      const updates: Partial<TypoCheckerState> = {
        history: updatedHistory,
        historyTotal: historyTotal - 1,
        deletingId: null,
      };

      if (selectedHistoryId === id) {
        updates.selectedHistoryId = null;
        updates.result = null;
      }

      set(updates);
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : '히스토리 삭제 중 오류가 발생했습니다';
      set({ historyError: errorMessage, deletingId: null });
    }
  },

  clearHistorySelection: () => {
    set({ selectedHistoryId: null, result: null });
  },
}));
