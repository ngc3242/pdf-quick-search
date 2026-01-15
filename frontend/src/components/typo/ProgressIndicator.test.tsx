import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProgressIndicator } from './ProgressIndicator';
import type { TypoCheckProgress } from '@/types';

describe('ProgressIndicator', () => {
  const mockOnCancel = vi.fn();
  const defaultProgress: TypoCheckProgress = {
    current_chunk: 2,
    total_chunks: 5,
    percentage: 40,
  };

  describe('Rendering', () => {
    it('should render progress container', () => {
      render(<ProgressIndicator progress={defaultProgress} onCancel={mockOnCancel} />);
      expect(screen.getByTestId('progress-indicator')).toBeInTheDocument();
    });

    it('should render progress bar', () => {
      render(<ProgressIndicator progress={defaultProgress} onCancel={mockOnCancel} />);
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('should render cancel button', () => {
      render(<ProgressIndicator progress={defaultProgress} onCancel={mockOnCancel} />);
      expect(screen.getByRole('button', { name: /취소|cancel/i })).toBeInTheDocument();
    });
  });

  describe('Progress display', () => {
    it('should display percentage', () => {
      render(<ProgressIndicator progress={defaultProgress} onCancel={mockOnCancel} />);
      expect(screen.getByText(/40%/)).toBeInTheDocument();
    });

    it('should display chunk progress', () => {
      render(<ProgressIndicator progress={defaultProgress} onCancel={mockOnCancel} />);
      expect(screen.getByText(/2.*5|2\/5/)).toBeInTheDocument();
    });

    it('should update progress bar width based on percentage', () => {
      render(<ProgressIndicator progress={defaultProgress} onCancel={mockOnCancel} />);
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '40');
    });

    it('should show 0% at start', () => {
      const startProgress: TypoCheckProgress = {
        current_chunk: 0,
        total_chunks: 5,
        percentage: 0,
      };
      render(<ProgressIndicator progress={startProgress} onCancel={mockOnCancel} />);
      expect(screen.getByText(/0%/)).toBeInTheDocument();
    });

    it('should show 100% when complete', () => {
      const completeProgress: TypoCheckProgress = {
        current_chunk: 5,
        total_chunks: 5,
        percentage: 100,
      };
      render(<ProgressIndicator progress={completeProgress} onCancel={mockOnCancel} />);
      expect(screen.getByText(/100%/)).toBeInTheDocument();
    });
  });

  describe('Progress bar animation', () => {
    it('should have progress bar fill element', () => {
      render(<ProgressIndicator progress={defaultProgress} onCancel={mockOnCancel} />);
      const progressBar = screen.getByRole('progressbar');
      const fillElement = progressBar.querySelector('[data-testid="progress-fill"]');
      expect(fillElement).toBeInTheDocument();
    });

    it('should set correct width style on progress fill', () => {
      render(<ProgressIndicator progress={defaultProgress} onCancel={mockOnCancel} />);
      const fillElement = screen.getByTestId('progress-fill');
      expect(fillElement).toHaveStyle({ width: '40%' });
    });
  });

  describe('Cancel functionality', () => {
    it('should call onCancel when cancel button is clicked', async () => {
      const user = userEvent.setup();
      render(<ProgressIndicator progress={defaultProgress} onCancel={mockOnCancel} />);

      const cancelButton = screen.getByRole('button', { name: /취소|cancel/i });
      await user.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    });
  });

  describe('Status message', () => {
    it('should display processing message', () => {
      render(<ProgressIndicator progress={defaultProgress} onCancel={mockOnCancel} />);
      expect(screen.getByText(/처리 중|검사 중|진행 중/i)).toBeInTheDocument();
    });

    it('should show custom status message when provided', () => {
      render(
        <ProgressIndicator
          progress={defaultProgress}
          onCancel={mockOnCancel}
          statusMessage="텍스트 분석 중..."
        />
      );
      expect(screen.getByText('텍스트 분석 중...')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have aria-valuemin on progressbar', () => {
      render(<ProgressIndicator progress={defaultProgress} onCancel={mockOnCancel} />);
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
    });

    it('should have aria-valuemax on progressbar', () => {
      render(<ProgressIndicator progress={defaultProgress} onCancel={mockOnCancel} />);
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    });

    it('should have aria-valuenow on progressbar', () => {
      render(<ProgressIndicator progress={defaultProgress} onCancel={mockOnCancel} />);
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '40');
    });

    it('should have accessible label for progressbar', () => {
      render(<ProgressIndicator progress={defaultProgress} onCancel={mockOnCancel} />);
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-label');
    });
  });
});
