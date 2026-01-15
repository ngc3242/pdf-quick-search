import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ReportDownload } from './ReportDownload';
import type { TypoCheckResult } from '@/types';

// Mock the typoApi
vi.mock('@/api', () => ({
  typoApi: {
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

describe('ReportDownload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock URL.createObjectURL and URL.revokeObjectURL
    global.URL.createObjectURL = vi.fn(() => 'blob:http://localhost/test');
    global.URL.revokeObjectURL = vi.fn();
  });

  describe('Rendering', () => {
    it('should render download buttons container', () => {
      render(<ReportDownload result={mockResult} />);
      expect(screen.getByTestId('report-download')).toBeInTheDocument();
    });

    it('should render HTML download button', () => {
      render(<ReportDownload result={mockResult} />);
      expect(screen.getByRole('button', { name: /HTML/i })).toBeInTheDocument();
    });

    it('should render PDF download button', () => {
      render(<ReportDownload result={mockResult} />);
      expect(screen.getByRole('button', { name: /PDF/i })).toBeInTheDocument();
    });
  });

  describe('Download functionality', () => {
    it('should call downloadReport with html format when HTML button clicked', async () => {
      const user = userEvent.setup();
      const mockBlob = new Blob(['<html></html>'], { type: 'text/html' });
      vi.mocked(typoApi.downloadReport).mockResolvedValue(mockBlob);

      render(<ReportDownload result={mockResult} />);

      const htmlButton = screen.getByRole('button', { name: /HTML/i });
      await user.click(htmlButton);

      expect(typoApi.downloadReport).toHaveBeenCalledWith(mockResult, 'html');
    });

    it('should call downloadReport with pdf format when PDF button clicked', async () => {
      const user = userEvent.setup();
      const mockBlob = new Blob(['%PDF-1.4'], { type: 'application/pdf' });
      vi.mocked(typoApi.downloadReport).mockResolvedValue(mockBlob);

      render(<ReportDownload result={mockResult} />);

      const pdfButton = screen.getByRole('button', { name: /PDF/i });
      await user.click(pdfButton);

      expect(typoApi.downloadReport).toHaveBeenCalledWith(mockResult, 'pdf');
    });

    it('should create blob URL for download', async () => {
      const user = userEvent.setup();
      const mockBlob = new Blob(['<html></html>'], { type: 'text/html' });
      vi.mocked(typoApi.downloadReport).mockResolvedValue(mockBlob);

      render(<ReportDownload result={mockResult} />);

      const htmlButton = screen.getByRole('button', { name: /HTML/i });
      await user.click(htmlButton);

      await waitFor(() => {
        expect(URL.createObjectURL).toHaveBeenCalledWith(mockBlob);
      });
    });
  });

  describe('Loading state', () => {
    it('should show loading indicator on HTML button while downloading', async () => {
      const user = userEvent.setup();
      // Create a promise that doesn't resolve immediately
      let resolvePromise: (value: Blob) => void = () => {};
      vi.mocked(typoApi.downloadReport).mockImplementation(
        () => new Promise((resolve) => { resolvePromise = resolve; })
      );

      render(<ReportDownload result={mockResult} />);

      const htmlButton = screen.getByRole('button', { name: /HTML/i });
      await user.click(htmlButton);

      // Button should show loading state (disabled)
      await waitFor(() => {
        expect(htmlButton).toBeDisabled();
      });

      // Cleanup: resolve the promise
      resolvePromise(new Blob());
    });

    it('should disable PDF button while HTML is downloading', async () => {
      const user = userEvent.setup();
      vi.mocked(typoApi.downloadReport).mockImplementation(
        () => new Promise(() => {})
      );

      render(<ReportDownload result={mockResult} />);

      const htmlButton = screen.getByRole('button', { name: /HTML/i });
      const pdfButton = screen.getByRole('button', { name: /PDF/i });

      await user.click(htmlButton);

      await waitFor(() => {
        expect(pdfButton).toBeDisabled();
      });
    });
  });

  describe('Error handling', () => {
    it('should show error message on download failure', async () => {
      const user = userEvent.setup();
      vi.mocked(typoApi.downloadReport).mockRejectedValue(new Error('Download failed'));

      render(<ReportDownload result={mockResult} />);

      const htmlButton = screen.getByRole('button', { name: /HTML/i });
      await user.click(htmlButton);

      await waitFor(() => {
        expect(screen.getByText(/다운로드.*오류|오류.*다운로드/i)).toBeInTheDocument();
      });
    });

    it('should re-enable buttons after error', async () => {
      const user = userEvent.setup();
      vi.mocked(typoApi.downloadReport).mockRejectedValue(new Error('Download failed'));

      render(<ReportDownload result={mockResult} />);

      const htmlButton = screen.getByRole('button', { name: /HTML/i });
      await user.click(htmlButton);

      await waitFor(() => {
        expect(htmlButton).not.toBeDisabled();
      });
    });
  });

  describe('Disabled state', () => {
    it('should disable all buttons when disabled prop is true', () => {
      render(<ReportDownload result={mockResult} disabled />);

      expect(screen.getByRole('button', { name: /HTML/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /PDF/i })).toBeDisabled();
    });
  });
});
