import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { SignupPage } from './SignupPage';

// Mock the authApi
vi.mock('@/api/authApi', () => ({
  authApi: {
    signup: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

import { authApi } from '@/api/authApi';

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('SignupPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Form rendering', () => {
    it('should render the page title', () => {
      renderWithRouter(<SignupPage />);
      expect(screen.getByRole('heading', { level: 1, name: /create account/i })).toBeInTheDocument();
    });

    it('should render email input field', () => {
      renderWithRouter(<SignupPage />);
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    });

    it('should render name input field', () => {
      renderWithRouter(<SignupPage />);
      expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument();
    });

    it('should render phone input field', () => {
      renderWithRouter(<SignupPage />);
      expect(screen.getByLabelText(/^phone$/i)).toBeInTheDocument();
    });

    it('should render password input field', () => {
      renderWithRouter(<SignupPage />);
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    });

    it('should render password confirm input field', () => {
      renderWithRouter(<SignupPage />);
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    });

    it('should render submit button', () => {
      renderWithRouter(<SignupPage />);
      expect(screen.getByRole('button', { name: /sign up/i })).toBeInTheDocument();
    });

    it('should render login link', () => {
      renderWithRouter(<SignupPage />);
      expect(screen.getByRole('link', { name: /log in/i })).toBeInTheDocument();
    });
  });

  describe('Form validation', () => {
    it('should show error when email is empty', async () => {
      const user = userEvent.setup();
      renderWithRouter(<SignupPage />);

      // Fill other fields but leave email empty
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/이메일을 입력해주세요/)).toBeInTheDocument();
      });
    });

    it('should show error when email format is invalid', async () => {
      const user = userEvent.setup();
      renderWithRouter(<SignupPage />);

      // Use 'test@test' which passes HTML5 email validation but fails our custom regex
      // (our regex requires a '.' after the '@': /^[^\s@]+@[^\s@]+\.[^\s@]+$/)
      await user.type(screen.getByLabelText(/email address/i), 'test@test');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/올바른 이메일 형식을 입력해주세요/)).toBeInTheDocument();
      });
    });

    it('should show error when name is empty', async () => {
      const user = userEvent.setup();
      renderWithRouter(<SignupPage />);

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/이름을 입력해주세요/)).toBeInTheDocument();
      });
    });

    it('should show error when name is too short', async () => {
      const user = userEvent.setup();
      renderWithRouter(<SignupPage />);

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'A');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/이름은 2자 이상/)).toBeInTheDocument();
      });
    });

    it('should show error when phone is empty', async () => {
      const user = userEvent.setup();
      renderWithRouter(<SignupPage />);

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/휴대폰번호를 입력해주세요/)).toBeInTheDocument();
      });
    });

    it('should show error when password is too short', async () => {
      const user = userEvent.setup();
      renderWithRouter(<SignupPage />);

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Pass1');
      await user.type(screen.getByLabelText(/confirm password/i), 'Pass1');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/비밀번호는 8자 이상이어야 합니다/)).toBeInTheDocument();
      });
    });

    it('should show error when password has no uppercase', async () => {
      const user = userEvent.setup();
      renderWithRouter(<SignupPage />);

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'password123');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/대문자를 포함해주세요/)).toBeInTheDocument();
      });
    });

    it('should show error when password has no lowercase', async () => {
      const user = userEvent.setup();
      renderWithRouter(<SignupPage />);

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'PASSWORD123');
      await user.type(screen.getByLabelText(/confirm password/i), 'PASSWORD123');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/소문자를 포함해주세요/)).toBeInTheDocument();
      });
    });

    it('should show error when password has no number', async () => {
      const user = userEvent.setup();
      renderWithRouter(<SignupPage />);

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Passwordabc');
      await user.type(screen.getByLabelText(/confirm password/i), 'Passwordabc');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/숫자를 포함해주세요/)).toBeInTheDocument();
      });
    });

    it('should show error when passwords do not match', async () => {
      const user = userEvent.setup();
      renderWithRouter(<SignupPage />);

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password456');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/비밀번호가 일치하지 않습니다/)).toBeInTheDocument();
      });
    });
  });

  describe('Loading state', () => {
    it('should disable submit button during loading', async () => {
      const user = userEvent.setup();

      // Mock signup to return a promise that doesn't resolve immediately
      vi.mocked(authApi.signup).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      renderWithRouter(<SignupPage />);

      // Fill form with valid data
      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123');

      // Click submit
      const submitButton = screen.getByRole('button', { name: /sign up/i });
      await user.click(submitButton);

      // Button should be disabled during loading
      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });
    });

    it('should disable form inputs during loading', async () => {
      const user = userEvent.setup();

      vi.mocked(authApi.signup).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      renderWithRouter(<SignupPage />);

      // Fill form with valid data
      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeDisabled();
        expect(screen.getByLabelText(/^name$/i)).toBeDisabled();
        expect(screen.getByLabelText(/^phone$/i)).toBeDisabled();
      });
    });
  });

  describe('Successful signup', () => {
    it('should show success message after successful signup', async () => {
      const user = userEvent.setup();

      vi.mocked(authApi.signup).mockResolvedValue({
        message: 'Signup successful',
        user: {
          id: '1',
          email: 'test@example.com',
          name: 'Test User',
          approval_status: 'pending',
        },
      });

      renderWithRouter(<SignupPage />);

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/회원가입 완료/)).toBeInTheDocument();
      });
    });

    it('should show approval pending message after successful signup', async () => {
      const user = userEvent.setup();

      vi.mocked(authApi.signup).mockResolvedValue({
        message: 'Signup successful',
        user: {
          id: '1',
          email: 'test@example.com',
          name: 'Test User',
          approval_status: 'pending',
        },
      });

      renderWithRouter(<SignupPage />);

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/관리자 승인 후 로그인이 가능합니다/)).toBeInTheDocument();
      });
    });
  });

  describe('Server error handling', () => {
    it('should show duplicate email error when server returns 409', async () => {
      const user = userEvent.setup();

      vi.mocked(authApi.signup).mockRejectedValue({
        response: {
          status: 409,
          data: { error: '이미 등록된 이메일입니다' },
        },
      });

      renderWithRouter(<SignupPage />);

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/이미 등록된 이메일입니다/)).toBeInTheDocument();
      });
    });

    it('should show validation error when server returns 400', async () => {
      const user = userEvent.setup();

      vi.mocked(authApi.signup).mockRejectedValue({
        response: {
          status: 400,
          data: { error: '전화번호 형식이 올바르지 않습니다' },
        },
      });

      renderWithRouter(<SignupPage />);

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/전화번호 형식이 올바르지 않습니다/)).toBeInTheDocument();
      });
    });

    it('should show generic error for server error', async () => {
      const user = userEvent.setup();

      vi.mocked(authApi.signup).mockRejectedValue({
        response: {
          status: 500,
          data: {},
        },
      });

      renderWithRouter(<SignupPage />);

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/회원가입 중 오류가 발생했습니다/)).toBeInTheDocument();
      });
    });

    it('should show network error message', async () => {
      const user = userEvent.setup();

      vi.mocked(authApi.signup).mockRejectedValue(new Error('Network Error'));

      renderWithRouter(<SignupPage />);

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^name$/i), 'Test User');
      await user.type(screen.getByLabelText(/^phone$/i), '010-1234-5678');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123');

      await user.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/네트워크 오류가 발생했습니다/)).toBeInTheDocument();
      });
    });
  });

  describe('Password visibility toggle', () => {
    it('should toggle password visibility when clicking visibility button', async () => {
      const user = userEvent.setup();
      renderWithRouter(<SignupPage />);

      const passwordInput = screen.getByLabelText(/^password$/i);
      expect(passwordInput).toHaveAttribute('type', 'password');

      // Find visibility toggle button (there are 2 for password and confirm)
      const toggleButtons = screen.getAllByRole('button').filter(
        button => button.querySelector('.material-symbols-outlined')
      );

      // First toggle button is for password field
      await user.click(toggleButtons[0]);
      expect(passwordInput).toHaveAttribute('type', 'text');

      await user.click(toggleButtons[0]);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });
  });
});
