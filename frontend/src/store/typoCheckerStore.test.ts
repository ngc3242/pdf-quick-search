import { describe, it, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';
import { useTypoCheckerStore } from './typoCheckerStore';
import type { TypoCheckResult, TypoProvider } from '@/types';

// Mock the typo API
vi.mock('@/api', () => ({
  typoApi: {
    checkTypo: vi.fn(),
    getProviderAvailability: vi.fn(),
  },
}));

import { typoApi } from '@/api';

const mockTypoResult: TypoCheckResult = {
  original_text: '안녕하세요 반갑슴니다',
  corrected_text: '안녕하세요 반갑습니다',
  issues: [
    {
      original: '반갑슴니다',
      corrected: '반갑습니다',
      position: { start: 6, end: 11 },
      type: 'spelling',
      explanation: '맞춤법 오류: "슴"을 "습"으로 수정',
    },
  ],
  provider: 'claude',
  processing_time_ms: 1500,
  chunk_count: 1,
};

describe('useTypoCheckerStore', () => {
  beforeEach(() => {
    // Reset the store before each test
    const { reset } = useTypoCheckerStore.getState();
    reset();
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useTypoCheckerStore.getState();

      expect(state.text).toBe('');
      expect(state.result).toBeNull();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
      expect(state.selectedProvider).toBe('claude');
      expect(state.progress).toBeNull();
    });
  });

  describe('setText', () => {
    it('should update text state', () => {
      const { setText } = useTypoCheckerStore.getState();

      act(() => {
        setText('테스트 텍스트입니다');
      });

      expect(useTypoCheckerStore.getState().text).toBe('테스트 텍스트입니다');
    });

    it('should clear error when setting new text', () => {
      // Set an error first
      useTypoCheckerStore.setState({ error: 'Some error' });

      const { setText } = useTypoCheckerStore.getState();

      act(() => {
        setText('새로운 텍스트');
      });

      expect(useTypoCheckerStore.getState().error).toBeNull();
    });
  });

  describe('setProvider', () => {
    it('should update selectedProvider state', () => {
      const { setProvider } = useTypoCheckerStore.getState();

      act(() => {
        setProvider('openai');
      });

      expect(useTypoCheckerStore.getState().selectedProvider).toBe('openai');
    });

    it('should accept all valid provider values', () => {
      const { setProvider } = useTypoCheckerStore.getState();
      const providers: TypoProvider[] = ['claude', 'openai', 'gemini'];

      providers.forEach((provider) => {
        act(() => {
          setProvider(provider);
        });
        expect(useTypoCheckerStore.getState().selectedProvider).toBe(provider);
      });
    });
  });

  describe('checkTypo', () => {
    it('should set isLoading to true when checking starts', async () => {
      vi.mocked(typoApi.checkTypo).mockImplementation(
        () => new Promise(() => {}) // Never resolves to test loading state
      );

      const { checkTypo, setText } = useTypoCheckerStore.getState();

      act(() => {
        setText('테스트 텍스트');
      });

      // Start check but don't await
      act(() => {
        checkTypo();
      });

      expect(useTypoCheckerStore.getState().isLoading).toBe(true);
    });

    it('should update result on successful check', async () => {
      vi.mocked(typoApi.checkTypo).mockResolvedValue(mockTypoResult);

      const { checkTypo, setText } = useTypoCheckerStore.getState();

      act(() => {
        setText('안녕하세요 반갑슴니다');
      });

      await act(async () => {
        await checkTypo();
      });

      const state = useTypoCheckerStore.getState();
      expect(state.result).toEqual(mockTypoResult);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should set error on failed check', async () => {
      const errorMessage = '서버 오류가 발생했습니다';
      vi.mocked(typoApi.checkTypo).mockRejectedValue(new Error(errorMessage));

      const { checkTypo, setText } = useTypoCheckerStore.getState();

      act(() => {
        setText('테스트 텍스트');
      });

      await act(async () => {
        await checkTypo();
      });

      const state = useTypoCheckerStore.getState();
      expect(state.error).toBe(errorMessage);
      expect(state.isLoading).toBe(false);
      expect(state.result).toBeNull();
    });

    it('should call API with correct parameters', async () => {
      vi.mocked(typoApi.checkTypo).mockResolvedValue(mockTypoResult);

      const { checkTypo, setText, setProvider } = useTypoCheckerStore.getState();

      act(() => {
        setText('테스트 텍스트');
        setProvider('gemini');
      });

      await act(async () => {
        await checkTypo();
      });

      expect(typoApi.checkTypo).toHaveBeenCalledWith({
        text: '테스트 텍스트',
        provider: 'gemini',
      });
    });

    it('should not call API if text is empty', async () => {
      const { checkTypo } = useTypoCheckerStore.getState();

      await act(async () => {
        await checkTypo();
      });

      expect(typoApi.checkTypo).not.toHaveBeenCalled();
    });
  });

  describe('setProgress', () => {
    it('should update progress state', () => {
      const { setProgress } = useTypoCheckerStore.getState();

      act(() => {
        setProgress({
          current_chunk: 2,
          total_chunks: 5,
          percentage: 40,
        });
      });

      const state = useTypoCheckerStore.getState();
      expect(state.progress).toEqual({
        current_chunk: 2,
        total_chunks: 5,
        percentage: 40,
      });
    });
  });

  describe('cancelCheck', () => {
    it('should reset loading state and set cancelled flag', () => {
      // Set loading state
      useTypoCheckerStore.setState({ isLoading: true });

      const { cancelCheck } = useTypoCheckerStore.getState();

      act(() => {
        cancelCheck();
      });

      const state = useTypoCheckerStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.progress).toBeNull();
    });
  });

  describe('reset', () => {
    it('should reset all state to initial values', () => {
      // Set some state
      useTypoCheckerStore.setState({
        text: 'Some text',
        result: mockTypoResult,
        isLoading: true,
        error: 'Some error',
        selectedProvider: 'openai',
        progress: { current_chunk: 1, total_chunks: 3, percentage: 33 },
      });

      const { reset } = useTypoCheckerStore.getState();

      act(() => {
        reset();
      });

      const state = useTypoCheckerStore.getState();
      expect(state.text).toBe('');
      expect(state.result).toBeNull();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
      expect(state.selectedProvider).toBe('claude');
      expect(state.progress).toBeNull();
    });
  });

  describe('clearError', () => {
    it('should clear error state', () => {
      useTypoCheckerStore.setState({ error: 'Some error' });

      const { clearError } = useTypoCheckerStore.getState();

      act(() => {
        clearError();
      });

      expect(useTypoCheckerStore.getState().error).toBeNull();
    });
  });
});
