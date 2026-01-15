import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { HistoryPanel } from './HistoryPanel';
import type { TypoHistoryItem } from '@/types';

// Mock window.confirm
const mockConfirm = vi.fn();
window.confirm = mockConfirm;

describe('HistoryPanel', () => {
  const mockHistoryItems: TypoHistoryItem[] = [
    {
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
    },
    {
      id: 2,
      corrected_text: '테스트 텍스트입니다',
      issues: [],
      provider: 'gemini',
      created_at: '2026-01-14T09:00:00Z',
      issue_count: 0,
    },
  ];

  const defaultProps = {
    history: mockHistoryItems,
    isLoading: false,
    error: null,
    selectedHistoryId: null,
    deletingId: null,
    onSelect: vi.fn(),
    onDelete: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockConfirm.mockReturnValue(true);
  });

  describe('Loading State', () => {
    it('should show loading skeleton when isLoading is true (REQ-S-001)', () => {
      render(<HistoryPanel {...defaultProps} isLoading={true} history={[]} />);

      const skeletons = screen.getAllByTestId('history-skeleton');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  describe('Empty State', () => {
    it('should show empty state message when history is empty (REQ-S-002)', () => {
      render(<HistoryPanel {...defaultProps} history={[]} />);

      expect(screen.getByText(/검사 기록이 없습니다/)).toBeInTheDocument();
    });
  });

  describe('History List Display', () => {
    it('should display history items with date, provider, and issue count (REQ-U-002)', () => {
      render(<HistoryPanel {...defaultProps} />);

      // Check first item
      expect(screen.getByText(/Claude/i)).toBeInTheDocument();
      expect(screen.getByText(/1개/)).toBeInTheDocument();

      // Check second item
      expect(screen.getByText(/Gemini/i)).toBeInTheDocument();
      expect(screen.getByText(/0개/)).toBeInTheDocument();
    });

    it('should display formatted date for each history item', () => {
      render(<HistoryPanel {...defaultProps} />);

      // Should display date in Korean format
      expect(screen.getByText(/2026.*1.*15/)).toBeInTheDocument();
    });
  });

  describe('Selection', () => {
    it('should call onSelect when clicking a history item (REQ-U-003)', () => {
      const onSelect = vi.fn();
      render(<HistoryPanel {...defaultProps} onSelect={onSelect} />);

      const historyItems = screen.getAllByTestId('history-item');
      fireEvent.click(historyItems[0]);

      expect(onSelect).toHaveBeenCalledWith(1);
    });

    it('should highlight selected history item', () => {
      render(<HistoryPanel {...defaultProps} selectedHistoryId={1} />);

      const historyItems = screen.getAllByTestId('history-item');
      expect(historyItems[0]).toHaveClass('bg-blue-50');
    });
  });

  describe('Delete', () => {
    it('should show delete button for each history item (REQ-U-004)', () => {
      render(<HistoryPanel {...defaultProps} />);

      const deleteButtons = screen.getAllByTestId('delete-button');
      expect(deleteButtons.length).toBe(2);
    });

    it('should show confirmation dialog before delete (REQ-N-002)', () => {
      const onDelete = vi.fn();
      render(<HistoryPanel {...defaultProps} onDelete={onDelete} />);

      const deleteButtons = screen.getAllByTestId('delete-button');
      fireEvent.click(deleteButtons[0]);

      expect(mockConfirm).toHaveBeenCalled();
    });

    it('should call onDelete when confirmed (REQ-N-002)', () => {
      mockConfirm.mockReturnValue(true);
      const onDelete = vi.fn();
      render(<HistoryPanel {...defaultProps} onDelete={onDelete} />);

      const deleteButtons = screen.getAllByTestId('delete-button');
      fireEvent.click(deleteButtons[0]);

      expect(onDelete).toHaveBeenCalledWith(1);
    });

    it('should not call onDelete when cancelled', () => {
      mockConfirm.mockReturnValue(false);
      const onDelete = vi.fn();
      render(<HistoryPanel {...defaultProps} onDelete={onDelete} />);

      const deleteButtons = screen.getAllByTestId('delete-button');
      fireEvent.click(deleteButtons[0]);

      expect(onDelete).not.toHaveBeenCalled();
    });

    it('should show loading state on delete button when deletingId matches (REQ-S-003)', () => {
      render(<HistoryPanel {...defaultProps} deletingId={1} />);

      const deleteButtons = screen.getAllByTestId('delete-button');
      expect(deleteButtons[0]).toBeDisabled();
      expect(deleteButtons[0]).toHaveClass('opacity-50');
    });
  });

  describe('Error State', () => {
    it('should display error message when error is present', () => {
      render(<HistoryPanel {...defaultProps} error="히스토리 로드 실패" />);

      expect(screen.getByText(/히스토리 로드 실패/)).toBeInTheDocument();
    });
  });

  describe('Preview Text', () => {
    it('should show truncated corrected text as preview', () => {
      const longText = '이것은 매우 긴 텍스트입니다. '.repeat(10);
      const historyWithLongText: TypoHistoryItem[] = [
        {
          ...mockHistoryItems[0],
          corrected_text: longText,
        },
      ];

      render(<HistoryPanel {...defaultProps} history={historyWithLongText} />);

      // Should truncate long text
      const previewElement = screen.getByTestId('history-preview');
      expect(previewElement.textContent?.length).toBeLessThan(longText.length);
    });
  });
});
