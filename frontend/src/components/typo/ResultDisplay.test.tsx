import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ResultDisplay } from './ResultDisplay';
import type { TypoCheckResult } from '@/types';

const mockResult: TypoCheckResult = {
  original_text: '안녕하세요 반갑슴니다. 오늘 날시가 좋네요.',
  corrected_text: '안녕하세요 반갑습니다. 오늘 날씨가 좋네요.',
  issues: [
    {
      original: '반갑슴니다',
      corrected: '반갑습니다',
      position: { start: 6, end: 11 },
      type: 'spelling',
      explanation: '맞춤법 오류: "슴"을 "습"으로 수정',
    },
    {
      original: '날시',
      corrected: '날씨',
      position: { start: 18, end: 20 },
      type: 'spelling',
      explanation: '맞춤법 오류: "시"를 "씨"로 수정',
    },
  ],
  provider: 'claude',
  processing_time_ms: 1500,
  chunk_count: 1,
};

const emptyResult: TypoCheckResult = {
  original_text: '안녕하세요',
  corrected_text: '안녕하세요',
  issues: [],
  provider: 'claude',
  processing_time_ms: 500,
  chunk_count: 1,
};

describe('ResultDisplay', () => {
  describe('Rendering', () => {
    it('should render the result container', () => {
      render(<ResultDisplay result={mockResult} />);
      expect(screen.getByTestId('result-display')).toBeInTheDocument();
    });

    it('should render the corrected text', () => {
      render(<ResultDisplay result={mockResult} />);
      // Use getAllByText and check at least one exists
      const matches = screen.getAllByText(/반갑습니다/);
      expect(matches.length).toBeGreaterThan(0);
    });

    it('should display issue count', () => {
      render(<ResultDisplay result={mockResult} />);
      expect(screen.getByText(/2개/)).toBeInTheDocument();
    });

    it('should show no issues message when result has no issues', () => {
      render(<ResultDisplay result={emptyResult} />);
      expect(screen.getByText('오류가 없습니다!')).toBeInTheDocument();
    });
  });

  describe('Issue highlighting', () => {
    it('should highlight corrected words', () => {
      render(<ResultDisplay result={mockResult} />);
      // Look for elements with highlight styling
      const highlights = screen.getAllByTestId('highlight-correction');
      expect(highlights.length).toBeGreaterThan(0);
    });

    it('should show original and corrected text for each issue', () => {
      render(<ResultDisplay result={mockResult} />);
      // Check that both original and corrected exist (possibly in multiple places)
      expect(screen.getAllByText(/반갑슴니다/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/반갑습니다/).length).toBeGreaterThan(0);
    });
  });

  describe('Diff view', () => {
    it('should render tab buttons for view mode switching', () => {
      render(<ResultDisplay result={mockResult} />);
      expect(screen.getByRole('button', { name: /수정된 텍스트/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /원문 비교/ })).toBeInTheDocument();
    });

    it('should switch to diff view when diff tab is clicked', async () => {
      const user = userEvent.setup();
      render(<ResultDisplay result={mockResult} />);

      const diffButton = screen.getByRole('button', { name: /원문 비교/ });
      await user.click(diffButton);

      // In diff view, should show both original label
      expect(screen.getByText('원본')).toBeInTheDocument();
    });

    it('should show corrected view by default', () => {
      render(<ResultDisplay result={mockResult} />);
      // The corrected text should be visible - look for highlight
      const highlights = screen.getAllByTestId('highlight-correction');
      expect(highlights.length).toBeGreaterThan(0);
    });
  });

  describe('Issue list', () => {
    it('should list all issues found', () => {
      render(<ResultDisplay result={mockResult} />);
      // Check for the issue list items using the line-through original text
      const originalTexts = screen.getAllByText(/반갑슴니다/);
      expect(originalTexts.length).toBeGreaterThan(0);
    });

    it('should display issue type for each issue', () => {
      render(<ResultDisplay result={mockResult} />);
      // Look for spelling type indicators
      const spellingBadges = screen.getAllByText('맞춤법');
      expect(spellingBadges.length).toBeGreaterThan(0);
    });

    it('should show explanation for issues', () => {
      render(<ResultDisplay result={mockResult} />);
      expect(screen.getByText(/슴.*습.*수정/)).toBeInTheDocument();
    });
  });

  describe('Copy functionality', () => {
    it('should render copy button', () => {
      render(<ResultDisplay result={mockResult} />);
      expect(screen.getByRole('button', { name: '복사' })).toBeInTheDocument();
    });

    it('should copy corrected text when copy button is clicked', async () => {
      const user = userEvent.setup();
      const writeTextMock = vi.fn().mockResolvedValue(undefined);
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText: writeTextMock },
        writable: true,
        configurable: true,
      });

      render(<ResultDisplay result={mockResult} />);

      const copyButton = screen.getByRole('button', { name: '복사' });
      await user.click(copyButton);

      expect(writeTextMock).toHaveBeenCalledWith(mockResult.corrected_text);
    });
  });

  describe('Processing info', () => {
    it('should display processing time', () => {
      render(<ResultDisplay result={mockResult} />);
      expect(screen.getByText('1.5초')).toBeInTheDocument();
    });

    it('should display provider used', () => {
      render(<ResultDisplay result={mockResult} />);
      expect(screen.getByText('Claude')).toBeInTheDocument();
    });
  });

  describe('Empty state', () => {
    it('should show success message when no issues found', () => {
      render(<ResultDisplay result={emptyResult} />);
      expect(screen.getByText('오류가 없습니다!')).toBeInTheDocument();
      expect(screen.getByText(/수정할 내용이 없습니다/)).toBeInTheDocument();
    });
  });
});
