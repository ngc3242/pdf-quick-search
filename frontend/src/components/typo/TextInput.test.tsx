import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TextInput } from './TextInput';

describe('TextInput', () => {
  const mockOnChange = vi.fn();
  const defaultProps = {
    value: '',
    onChange: mockOnChange,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render textarea element', () => {
      render(<TextInput {...defaultProps} />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('should render with placeholder text', () => {
      render(<TextInput {...defaultProps} placeholder="텍스트를 입력하세요" />);
      expect(screen.getByPlaceholderText('텍스트를 입력하세요')).toBeInTheDocument();
    });

    it('should display character count', () => {
      render(<TextInput {...defaultProps} value="테스트" />);
      // Check the character count container contains "3"
      const charCountContainer = screen.getByText(/자$/).parentElement;
      expect(charCountContainer?.textContent).toContain('3');
    });

    it('should show max character limit', () => {
      render(<TextInput {...defaultProps} maxLength={100000} />);
      const charCountContainer = screen.getByText(/자$/).parentElement;
      expect(charCountContainer?.textContent).toContain('100,000');
    });
  });

  describe('Character counting', () => {
    it('should display current character count', () => {
      const text = '안녕하세요';
      render(<TextInput {...defaultProps} value={text} />);
      const charCountContainer = screen.getByText(/자$/).parentElement;
      expect(charCountContainer?.textContent).toContain('5');
    });

    it('should update character count as text changes', async () => {
      const { rerender } = render(<TextInput {...defaultProps} value="" />);
      let charCountContainer = screen.getByText(/자$/).parentElement;
      expect(charCountContainer?.textContent).toMatch(/^0/);

      rerender(<TextInput {...defaultProps} value="Hello" />);
      charCountContainer = screen.getByText(/자$/).parentElement;
      expect(charCountContainer?.textContent).toContain('5');
    });

    it('should format large character counts with commas', () => {
      const longText = 'a'.repeat(1234);
      render(<TextInput {...defaultProps} value={longText} />);
      const charCountContainer = screen.getByText(/자$/).parentElement;
      expect(charCountContainer?.textContent).toContain('1,234');
    });
  });

  describe('Character limit enforcement', () => {
    it('should enforce 100K character limit by default', () => {
      render(<TextInput {...defaultProps} />);
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      expect(textarea.maxLength).toBe(100000);
    });

    it('should allow custom maxLength', () => {
      render(<TextInput {...defaultProps} maxLength={50000} />);
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      expect(textarea.maxLength).toBe(50000);
    });

    it('should show warning styling when approaching limit', () => {
      const nearLimitText = 'a'.repeat(95000);
      render(<TextInput {...defaultProps} value={nearLimitText} maxLength={100000} />);
      const charCountContainer = screen.getByText(/자$/).parentElement;
      expect(charCountContainer).toHaveClass('text-yellow-600');
    });

    it('should show error styling when at limit', () => {
      const atLimitText = 'a'.repeat(100000);
      render(<TextInput {...defaultProps} value={atLimitText} maxLength={100000} />);
      const charCountContainer = screen.getByText(/자$/).parentElement;
      expect(charCountContainer).toHaveClass('text-red-600');
    });
  });

  describe('User interactions', () => {
    it('should call onChange when text is entered', async () => {
      const user = userEvent.setup();
      render(<TextInput {...defaultProps} />);

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, '테스트');

      expect(mockOnChange).toHaveBeenCalled();
    });

    it('should pass the entered text to onChange', async () => {
      const user = userEvent.setup();
      render(<TextInput {...defaultProps} />);

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'A');

      expect(mockOnChange).toHaveBeenCalledWith('A');
    });

    it('should be focusable', async () => {
      const user = userEvent.setup();
      render(<TextInput {...defaultProps} />);
      const textarea = screen.getByRole('textbox');

      await user.click(textarea);
      expect(textarea).toHaveFocus();
    });
  });

  describe('Disabled state', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<TextInput {...defaultProps} disabled />);
      expect(screen.getByRole('textbox')).toBeDisabled();
    });

    it('should not call onChange when disabled', async () => {
      const user = userEvent.setup();
      render(<TextInput {...defaultProps} disabled />);

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, '테스트');

      expect(mockOnChange).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible label', () => {
      render(<TextInput {...defaultProps} label="맞춤법 검사할 텍스트" />);
      expect(screen.getByLabelText('맞춤법 검사할 텍스트')).toBeInTheDocument();
    });

    it('should have aria-describedby for character count', () => {
      render(<TextInput {...defaultProps} />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('aria-describedby');
    });
  });
});
