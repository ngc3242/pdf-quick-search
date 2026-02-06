import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { TypoCheckerPage } from './TypoCheckerPage';
import { useTypoCheckerStore } from '@/store';
import type { TypoCheckResult, ProviderAvailability } from '@/types';

// Mock the store
vi.mock('@/store', () => ({
  useTypoCheckerStore: vi.fn(),
  useAuthStore: vi.fn(() => ({
    user: { id: '1', name: 'Test User', email: 'test@example.com', role: 'user' },
    token: 'test-token',
  })),
}));

// Mock the API
vi.mock('@/api', () => ({
  typoApi: {
    checkTypo: vi.fn(),
    getProviderAvailability: vi.fn(),
    downloadReport: vi.fn(),
  },
}));

import { typoApi } from '@/api';

const mockResult: TypoCheckResult = {
  original_text: '안녕하세요 반갑슴니다.',
  corrected_text: '안녕하세요 반갑습니다.',
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
  processing_time_ms: 1500,
  chunk_count: 1,
};

const mockProviderAvailability: ProviderAvailability = {
  claude: true,
  openai: true,
  gemini: false,
};

const createMockStore = (overrides = {}) => ({
  text: '',
  result: null,
  isLoading: false,
  error: null,
  selectedProvider: 'gemini' as const,
  progress: null,
  currentJobId: null,
  setText: vi.fn(),
  setProvider: vi.fn(),
  checkTypo: vi.fn(),
  setProgress: vi.fn(),
  cancelCheck: vi.fn(),
  reset: vi.fn(),
  clearError: vi.fn(),
  // History state and actions (SPEC-HISTORY-001)
  history: [],
  historyPage: 1,
  historyPerPage: 20,
  historyTotal: 0,
  historyPages: 0,
  isHistoryLoading: false,
  historyError: null,
  selectedHistoryId: null,
  deletingId: null,
  loadHistory: vi.fn(),
  selectHistory: vi.fn(),
  deleteHistory: vi.fn(),
  clearHistorySelection: vi.fn(),
  ...overrides,
});

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('TypoCheckerPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(typoApi.getProviderAvailability).mockResolvedValue(mockProviderAvailability);
  });

  describe('Rendering', () => {
    it('should render the page title', () => {
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore();
        return typeof selector === 'function' ? selector(store) : store;
      });

      renderWithRouter(<TypoCheckerPage />);
      expect(screen.getByRole('heading', { level: 1, name: /맞춤법 검사/ })).toBeInTheDocument();
    });

    it('should render text input area', () => {
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore();
        return typeof selector === 'function' ? selector(store) : store;
      });

      renderWithRouter(<TypoCheckerPage />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('should render provider selector', () => {
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore();
        return typeof selector === 'function' ? selector(store) : store;
      });

      renderWithRouter(<TypoCheckerPage />);
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('should render check button', () => {
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore();
        return typeof selector === 'function' ? selector(store) : store;
      });

      renderWithRouter(<TypoCheckerPage />);
      expect(screen.getByRole('button', { name: /검사하기/ })).toBeInTheDocument();
    });
  });

  describe('User interactions', () => {
    it('should call setText when typing in textarea', async () => {
      const mockSetText = vi.fn();
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore({ setText: mockSetText });
        return typeof selector === 'function' ? selector(store) : store;
      });

      const user = userEvent.setup();
      renderWithRouter(<TypoCheckerPage />);

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, '테스트');

      expect(mockSetText).toHaveBeenCalled();
    });

    it('should call setProvider when selecting a provider', async () => {
      const mockSetProvider = vi.fn();
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore({ setProvider: mockSetProvider });
        return typeof selector === 'function' ? selector(store) : store;
      });

      const user = userEvent.setup();
      renderWithRouter(<TypoCheckerPage />);

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'openai');

      expect(mockSetProvider).toHaveBeenCalledWith('openai');
    });

    it('should call checkTypo when check button is clicked', async () => {
      const mockCheckTypo = vi.fn();
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore({
          text: '테스트 텍스트',
          checkTypo: mockCheckTypo
        });
        return typeof selector === 'function' ? selector(store) : store;
      });

      const user = userEvent.setup();
      renderWithRouter(<TypoCheckerPage />);

      const checkButton = screen.getByRole('button', { name: /검사하기/ });
      await user.click(checkButton);

      expect(mockCheckTypo).toHaveBeenCalled();
    });
  });

  describe('Loading state', () => {
    it('should show progress indicator when loading', () => {
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore({
          isLoading: true,
          progress: { current_chunk: 1, total_chunks: 3, percentage: 33 },
        });
        return typeof selector === 'function' ? selector(store) : store;
      });

      renderWithRouter(<TypoCheckerPage />);
      expect(screen.getByTestId('progress-indicator')).toBeInTheDocument();
    });

    it('should disable check button when loading', () => {
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore({ isLoading: true });
        return typeof selector === 'function' ? selector(store) : store;
      });

      renderWithRouter(<TypoCheckerPage />);
      // When loading, button text changes to "검사 중..."
      expect(screen.getByRole('button', { name: /검사 중/ })).toBeDisabled();
    });

    it('should call cancelCheck when cancel is clicked during loading', async () => {
      const mockCancelCheck = vi.fn();
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore({
          isLoading: true,
          progress: { current_chunk: 1, total_chunks: 3, percentage: 33 },
          cancelCheck: mockCancelCheck,
        });
        return typeof selector === 'function' ? selector(store) : store;
      });

      const user = userEvent.setup();
      renderWithRouter(<TypoCheckerPage />);

      const cancelButton = screen.getByRole('button', { name: /취소|cancel/i });
      await user.click(cancelButton);

      expect(mockCancelCheck).toHaveBeenCalled();
    });
  });

  describe('Result display', () => {
    it('should show result display when result is available', () => {
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore({ result: mockResult });
        return typeof selector === 'function' ? selector(store) : store;
      });

      renderWithRouter(<TypoCheckerPage />);
      expect(screen.getByTestId('result-display')).toBeInTheDocument();
    });

    it('should show report download when result is available', () => {
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore({ result: mockResult });
        return typeof selector === 'function' ? selector(store) : store;
      });

      renderWithRouter(<TypoCheckerPage />);
      expect(screen.getByTestId('report-download')).toBeInTheDocument();
    });
  });

  describe('Error handling', () => {
    it('should display error message when error occurs', () => {
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore({ error: '서버 오류가 발생했습니다' });
        return typeof selector === 'function' ? selector(store) : store;
      });

      renderWithRouter(<TypoCheckerPage />);
      expect(screen.getByText(/서버 오류가 발생했습니다/)).toBeInTheDocument();
    });

    it('should have dismiss button for error', () => {
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore({ error: '서버 오류가 발생했습니다' });
        return typeof selector === 'function' ? selector(store) : store;
      });

      renderWithRouter(<TypoCheckerPage />);
      expect(screen.getByRole('button', { name: /닫기|dismiss|close/i })).toBeInTheDocument();
    });
  });

  describe('Empty state', () => {
    it('should disable check button when text is empty', () => {
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore({ text: '' });
        return typeof selector === 'function' ? selector(store) : store;
      });

      renderWithRouter(<TypoCheckerPage />);
      expect(screen.getByRole('button', { name: /검사하기/ })).toBeDisabled();
    });

    it('should enable check button when text is entered', () => {
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore({ text: '테스트 텍스트' });
        return typeof selector === 'function' ? selector(store) : store;
      });

      renderWithRouter(<TypoCheckerPage />);
      expect(screen.getByRole('button', { name: /검사하기/ })).not.toBeDisabled();
    });
  });

  describe('Reset functionality', () => {
    it('should call reset when reset button is clicked', async () => {
      const mockReset = vi.fn();
      vi.mocked(useTypoCheckerStore).mockImplementation((selector) => {
        const store = createMockStore({
          text: '테스트',
          result: mockResult,
          reset: mockReset
        });
        return typeof selector === 'function' ? selector(store) : store;
      });

      const user = userEvent.setup();
      renderWithRouter(<TypoCheckerPage />);

      const resetButton = screen.getByRole('button', { name: /새로 검사|초기화|reset|clear/i });
      await user.click(resetButton);

      expect(mockReset).toHaveBeenCalled();
    });
  });
});
