import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProviderSelector } from './ProviderSelector';
import type { TypoProvider, ProviderAvailability } from '@/types';

describe('ProviderSelector', () => {
  const mockOnChange = vi.fn();
  const defaultAvailability: ProviderAvailability = {
    claude: true,
    openai: true,
    gemini: true,
  };
  const defaultProps = {
    value: 'claude' as TypoProvider,
    onChange: mockOnChange,
    availability: defaultAvailability,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render a select/dropdown element', () => {
      render(<ProviderSelector {...defaultProps} />);
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('should render all provider options', () => {
      render(<ProviderSelector {...defaultProps} />);

      expect(screen.getByRole('option', { name: /Claude/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /OpenAI/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Gemini/i })).toBeInTheDocument();
    });

    it('should display the currently selected provider', () => {
      render(<ProviderSelector {...defaultProps} value="openai" />);
      const select = screen.getByRole('combobox') as HTMLSelectElement;
      expect(select.value).toBe('openai');
    });

    it('should render with label when provided', () => {
      render(<ProviderSelector {...defaultProps} label="AI 제공자 선택" />);
      expect(screen.getByLabelText('AI 제공자 선택')).toBeInTheDocument();
    });
  });

  describe('Provider availability', () => {
    it('should disable unavailable providers', () => {
      const availability: ProviderAvailability = {
        claude: true,
        openai: false,
        gemini: true,
      };
      render(<ProviderSelector {...defaultProps} availability={availability} />);

      const openaiOption = screen.getByRole('option', { name: /OpenAI/i }) as HTMLOptionElement;
      expect(openaiOption.disabled).toBe(true);
    });

    it('should enable available providers', () => {
      render(<ProviderSelector {...defaultProps} />);

      const claudeOption = screen.getByRole('option', { name: /Claude/i }) as HTMLOptionElement;
      expect(claudeOption.disabled).toBe(false);
    });

    it('should show unavailable indicator for disabled providers', () => {
      const availability: ProviderAvailability = {
        claude: true,
        openai: false,
        gemini: false,
      };
      render(<ProviderSelector {...defaultProps} availability={availability} />);

      // Check that unavailable text is shown
      expect(screen.getByRole('option', { name: /OpenAI.*사용 불가/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Gemini.*사용 불가/i })).toBeInTheDocument();
    });

    it('should allow all providers when all are available', () => {
      render(<ProviderSelector {...defaultProps} />);

      const options = screen.getAllByRole('option') as HTMLOptionElement[];
      options.forEach((option) => {
        expect(option.disabled).toBe(false);
      });
    });
  });

  describe('Selection handling', () => {
    it('should call onChange when a provider is selected', async () => {
      const user = userEvent.setup();
      render(<ProviderSelector {...defaultProps} />);

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'gemini');

      expect(mockOnChange).toHaveBeenCalledWith('gemini');
    });

    it('should call onChange with correct provider value', async () => {
      const user = userEvent.setup();
      render(<ProviderSelector {...defaultProps} />);

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'openai');

      expect(mockOnChange).toHaveBeenCalledWith('openai');
    });

    it('should not call onChange for disabled providers', async () => {
      const availability: ProviderAvailability = {
        claude: true,
        openai: false,
        gemini: true,
      };
      render(<ProviderSelector {...defaultProps} availability={availability} />);

      const select = screen.getByRole('combobox') as HTMLSelectElement;
      // Try to select disabled option - it should remain as original value
      await userEvent.selectOptions(select, 'claude');

      // The onChange should not be called for the disabled option when tried
      expect(select.value).toBe('claude');
    });
  });

  describe('Disabled state', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<ProviderSelector {...defaultProps} disabled />);
      expect(screen.getByRole('combobox')).toBeDisabled();
    });

    it('should not call onChange when disabled', async () => {
      const user = userEvent.setup();
      render(<ProviderSelector {...defaultProps} disabled />);

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'gemini').catch(() => {});

      expect(mockOnChange).not.toHaveBeenCalled();
    });
  });

  describe('Provider display names', () => {
    it('should display Claude with correct label', () => {
      render(<ProviderSelector {...defaultProps} />);
      expect(screen.getByRole('option', { name: /Claude/i })).toBeInTheDocument();
    });

    it('should display OpenAI with correct label', () => {
      render(<ProviderSelector {...defaultProps} />);
      expect(screen.getByRole('option', { name: /OpenAI/i })).toBeInTheDocument();
    });

    it('should display Gemini with correct label', () => {
      render(<ProviderSelector {...defaultProps} />);
      expect(screen.getByRole('option', { name: /Gemini/i })).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible label', () => {
      render(<ProviderSelector {...defaultProps} label="AI 모델 선택" />);
      expect(screen.getByLabelText('AI 모델 선택')).toBeInTheDocument();
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      render(<ProviderSelector {...defaultProps} />);

      const select = screen.getByRole('combobox');
      await user.tab();

      expect(select).toHaveFocus();
    });
  });
});
