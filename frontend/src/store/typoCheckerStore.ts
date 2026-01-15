import { create } from 'zustand';
import type {
  TypoCheckResult,
  TypoProvider,
  TypoCheckProgress,
} from '@/types';
import { typoApi } from '@/api';

interface TypoCheckerState {
  text: string;
  result: TypoCheckResult | null;
  isLoading: boolean;
  error: string | null;
  selectedProvider: TypoProvider;
  progress: TypoCheckProgress | null;

  // Actions
  setText: (text: string) => void;
  setProvider: (provider: TypoProvider) => void;
  checkTypo: () => Promise<void>;
  setProgress: (progress: TypoCheckProgress) => void;
  cancelCheck: () => void;
  reset: () => void;
  clearError: () => void;
}

const initialState = {
  text: '',
  result: null,
  isLoading: false,
  error: null,
  selectedProvider: 'claude' as TypoProvider,
  progress: null,
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

    set({ isLoading: true, error: null, result: null });

    try {
      const result = await typoApi.checkTypo({
        text,
        provider: selectedProvider,
      });
      set({ result, isLoading: false });
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : '맞춤법 검사 중 오류가 발생했습니다';
      set({ error: errorMessage, isLoading: false, result: null });
    }
  },

  setProgress: (progress: TypoCheckProgress) => {
    set({ progress });
  },

  cancelCheck: () => {
    set({ isLoading: false, progress: null });
  },

  reset: () => {
    set(initialState);
  },

  clearError: () => {
    set({ error: null });
  },
}));
