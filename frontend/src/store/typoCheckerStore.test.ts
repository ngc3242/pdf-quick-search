import { describe, it, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';
import { useTypoCheckerStore } from './typoCheckerStore';
import type { TypoCheckResult, TypoProvider, TypoHistoryItem, TypoHistoryResponse } from '@/types';

// Mock the typo API
vi.mock('@/api', () => ({
  typoApi: {
    checkTypo: vi.fn(),
    getProviderAvailability: vi.fn(),
    getHistory: vi.fn(),
    deleteHistoryItem: vi.fn(),
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

  // History-related tests (SPEC-HISTORY-001)
  describe('History State', () => {
    const mockHistoryItem: TypoHistoryItem = {
      id: 1,
      corrected_text: '안녕하세요 반갑습니다',
      issues: [
        {
          original: '반갑슴니다',
          corrected: '반갑습니다',
          position: { start: 6, end: 11 },
          type: 'spelling',
          explanation: '맞춤법 오류',
        },
      ],
      provider: 'claude',
      created_at: '2026-01-15T10:30:00Z',
      issue_count: 1,
    };

    const mockHistoryResponse: TypoHistoryResponse = {
      success: true,
      history: [mockHistoryItem],
      total: 1,
      page: 1,
      per_page: 20,
      pages: 1,
    };

    it('should have correct initial history state', () => {
      const state = useTypoCheckerStore.getState();

      expect(state.history).toEqual([]);
      expect(state.historyPage).toBe(1);
      expect(state.historyPerPage).toBe(20);
      expect(state.historyTotal).toBe(0);
      expect(state.historyPages).toBe(0);
      expect(state.isHistoryLoading).toBe(false);
      expect(state.historyError).toBeNull();
      expect(state.selectedHistoryId).toBeNull();
      expect(state.deletingId).toBeNull();
    });

    describe('loadHistory', () => {
      it('should set isHistoryLoading to true when loading starts', async () => {
        vi.mocked(typoApi.getHistory).mockImplementation(
          () => new Promise(() => {}) // Never resolves to test loading state
        );

        const { loadHistory } = useTypoCheckerStore.getState();

        act(() => {
          loadHistory();
        });

        expect(useTypoCheckerStore.getState().isHistoryLoading).toBe(true);
      });

      it('should update history state on successful load', async () => {
        vi.mocked(typoApi.getHistory).mockResolvedValue(mockHistoryResponse);

        const { loadHistory } = useTypoCheckerStore.getState();

        await act(async () => {
          await loadHistory();
        });

        const state = useTypoCheckerStore.getState();
        expect(state.history).toEqual(mockHistoryResponse.history);
        expect(state.historyTotal).toBe(mockHistoryResponse.total);
        expect(state.historyPage).toBe(mockHistoryResponse.page);
        expect(state.historyPages).toBe(mockHistoryResponse.pages);
        expect(state.isHistoryLoading).toBe(false);
        expect(state.historyError).toBeNull();
      });

      it('should set historyError on failed load', async () => {
        const errorMessage = '히스토리 로드 실패';
        vi.mocked(typoApi.getHistory).mockRejectedValue(new Error(errorMessage));

        const { loadHistory } = useTypoCheckerStore.getState();

        await act(async () => {
          await loadHistory();
        });

        const state = useTypoCheckerStore.getState();
        expect(state.historyError).toBe(errorMessage);
        expect(state.isHistoryLoading).toBe(false);
      });

      it('should call API with correct page parameter', async () => {
        vi.mocked(typoApi.getHistory).mockResolvedValue(mockHistoryResponse);

        const { loadHistory } = useTypoCheckerStore.getState();

        await act(async () => {
          await loadHistory(2);
        });

        expect(typoApi.getHistory).toHaveBeenCalledWith(2, 20);
      });
    });

    describe('selectHistory', () => {
      it('should update selectedHistoryId and result', () => {
        useTypoCheckerStore.setState({ history: [mockHistoryItem] });

        const { selectHistory } = useTypoCheckerStore.getState();

        act(() => {
          selectHistory(1);
        });

        const state = useTypoCheckerStore.getState();
        expect(state.selectedHistoryId).toBe(1);
        expect(state.result).not.toBeNull();
        expect(state.result?.corrected_text).toBe(mockHistoryItem.corrected_text);
      });

      it('should not update result if history item not found', () => {
        useTypoCheckerStore.setState({ history: [mockHistoryItem], result: null });

        const { selectHistory } = useTypoCheckerStore.getState();

        act(() => {
          selectHistory(999);
        });

        const state = useTypoCheckerStore.getState();
        expect(state.selectedHistoryId).toBe(999);
        expect(state.result).toBeNull();
      });
    });

    describe('deleteHistory', () => {
      it('should set deletingId when delete starts', async () => {
        vi.mocked(typoApi.deleteHistoryItem).mockImplementation(
          () => new Promise(() => {})
        );

        useTypoCheckerStore.setState({ history: [mockHistoryItem] });

        const { deleteHistory } = useTypoCheckerStore.getState();

        act(() => {
          deleteHistory(1);
        });

        expect(useTypoCheckerStore.getState().deletingId).toBe(1);
      });

      it('should remove item from history on successful delete', async () => {
        vi.mocked(typoApi.deleteHistoryItem).mockResolvedValue({
          success: true,
          message: '삭제 완료',
        });

        useTypoCheckerStore.setState({
          history: [mockHistoryItem, { ...mockHistoryItem, id: 2 }],
          historyTotal: 2,
        });

        const { deleteHistory } = useTypoCheckerStore.getState();

        await act(async () => {
          await deleteHistory(1);
        });

        const state = useTypoCheckerStore.getState();
        expect(state.history.length).toBe(1);
        expect(state.history[0].id).toBe(2);
        expect(state.historyTotal).toBe(1);
        expect(state.deletingId).toBeNull();
      });

      it('should clear selectedHistoryId if deleted item was selected', async () => {
        vi.mocked(typoApi.deleteHistoryItem).mockResolvedValue({
          success: true,
          message: '삭제 완료',
        });

        useTypoCheckerStore.setState({
          history: [mockHistoryItem],
          selectedHistoryId: 1,
          result: mockTypoResult,
        });

        const { deleteHistory } = useTypoCheckerStore.getState();

        await act(async () => {
          await deleteHistory(1);
        });

        const state = useTypoCheckerStore.getState();
        expect(state.selectedHistoryId).toBeNull();
        expect(state.result).toBeNull();
      });

      it('should set historyError on failed delete', async () => {
        const errorMessage = '삭제 실패';
        vi.mocked(typoApi.deleteHistoryItem).mockRejectedValue(new Error(errorMessage));

        useTypoCheckerStore.setState({ history: [mockHistoryItem] });

        const { deleteHistory } = useTypoCheckerStore.getState();

        await act(async () => {
          await deleteHistory(1);
        });

        const state = useTypoCheckerStore.getState();
        expect(state.historyError).toBe(errorMessage);
        expect(state.deletingId).toBeNull();
        expect(state.history.length).toBe(1); // Item should not be removed
      });
    });

    describe('clearHistorySelection', () => {
      it('should clear selectedHistoryId and result', () => {
        useTypoCheckerStore.setState({
          selectedHistoryId: 1,
          result: mockTypoResult,
        });

        const { clearHistorySelection } = useTypoCheckerStore.getState();

        act(() => {
          clearHistorySelection();
        });

        const state = useTypoCheckerStore.getState();
        expect(state.selectedHistoryId).toBeNull();
        expect(state.result).toBeNull();
      });
    });
  });
});
