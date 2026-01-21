import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authApi } from '@/api/authApi';

interface FormErrors {
  email?: string;
  name?: string;
  phone?: string;
  password?: string;
  passwordConfirm?: string;
}

export function SignupPage() {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [serverError, setServerError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const navigate = useNavigate();

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Email validation
    if (!email) {
      newErrors.email = '이메일을 입력해주세요';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = '올바른 이메일 형식을 입력해주세요';
    }

    // Name validation
    if (!name) {
      newErrors.name = '이름을 입력해주세요';
    } else if (name.length < 2 || name.length > 100) {
      newErrors.name = '이름은 2자 이상 100자 이하로 입력해주세요';
    }

    // Phone validation (Korean format)
    if (!phone) {
      newErrors.phone = '휴대폰번호를 입력해주세요';
    } else if (!/^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$/.test(phone.replace(/-/g, ''))) {
      newErrors.phone = '올바른 휴대폰번호 형식을 입력해주세요 (예: 010-1234-5678)';
    }

    // Password validation
    if (!password) {
      newErrors.password = '비밀번호를 입력해주세요';
    } else if (password.length < 8) {
      newErrors.password = '비밀번호는 8자 이상이어야 합니다';
    } else if (!/[A-Z]/.test(password)) {
      newErrors.password = '비밀번호에 대문자를 포함해주세요';
    } else if (!/[a-z]/.test(password)) {
      newErrors.password = '비밀번호에 소문자를 포함해주세요';
    } else if (!/[0-9]/.test(password)) {
      newErrors.password = '비밀번호에 숫자를 포함해주세요';
    }

    // Password confirm validation
    if (!passwordConfirm) {
      newErrors.passwordConfirm = '비밀번호 확인을 입력해주세요';
    } else if (password !== passwordConfirm) {
      newErrors.passwordConfirm = '비밀번호가 일치하지 않습니다';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setServerError('');

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      await authApi.signup({
        email,
        name,
        phone,
        password,
      });

      setIsSuccess(true);

      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (error: unknown) {
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number; data?: { error?: string } } };
        if (axiosError.response?.status === 409) {
          setServerError('이미 등록된 이메일입니다.');
        } else if (axiosError.response?.status === 400) {
          setServerError(axiosError.response.data?.error || '입력 정보를 확인해주세요.');
        } else {
          setServerError('회원가입 중 오류가 발생했습니다. 다시 시도해주세요.');
        }
      } else {
        setServerError('네트워크 오류가 발생했습니다. 다시 시도해주세요.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="bg-white min-h-screen font-display flex flex-col">
        {/* Header */}
        <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-b-[#f0f2f4] px-6 lg:px-10 py-4 sticky top-0 bg-white/95 backdrop-blur-sm z-20">
          <div className="flex items-center gap-3 text-text-primary">
            <div className="size-8 text-primary">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                <path
                  clipRule="evenodd"
                  d="M12.0799 24L4 19.2479L9.95537 8.75216L18.04 13.4961L18.0446 4H29.9554L29.96 13.4961L38.0446 8.75216L44 19.2479L35.92 24L44 28.7521L38.0446 39.2479L29.96 34.5039L29.9554 44H18.0446L18.04 34.5039L9.95537 39.2479L4 28.7521L12.0799 24Z"
                  fill="currentColor"
                  fillRule="evenodd"
                />
              </svg>
            </div>
            <h2 className="text-lg font-bold leading-tight tracking-[-0.015em] hidden sm:block">PDF Quick Search</h2>
          </div>
        </header>

        {/* Success Message */}
        <main className="flex-1 flex flex-col items-center justify-center py-12 px-4 sm:px-6">
          <div className="w-full max-w-[440px] flex flex-col text-center">
            <div className="mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100">
                <span className="material-symbols-outlined text-[32px] text-green-600">check_circle</span>
              </div>
            </div>
            <h1 className="text-text-primary tracking-tight text-[28px] font-bold leading-tight mb-4">
              회원가입 완료
            </h1>
            <p className="text-text-secondary text-base font-normal leading-normal mb-8">
              회원가입이 완료되었습니다.<br />
              관리자 승인 후 로그인이 가능합니다.
            </p>
            <p className="text-text-secondary text-sm">
              잠시 후 로그인 페이지로 이동합니다...
            </p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="bg-white min-h-screen font-display flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-b-[#f0f2f4] px-6 lg:px-10 py-4 sticky top-0 bg-white/95 backdrop-blur-sm z-20">
        <div className="flex items-center gap-3 text-text-primary">
          <div className="size-8 text-primary">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
              <path
                clipRule="evenodd"
                d="M12.0799 24L4 19.2479L9.95537 8.75216L18.04 13.4961L18.0446 4H29.9554L29.96 13.4961L38.0446 8.75216L44 19.2479L35.92 24L44 28.7521L38.0446 39.2479L29.96 34.5039L29.9554 44H18.0446L18.04 34.5039L9.95537 39.2479L4 28.7521L12.0799 24Z"
                fill="currentColor"
                fillRule="evenodd"
              />
            </svg>
          </div>
          <h2 className="text-lg font-bold leading-tight tracking-[-0.015em] hidden sm:block">PDF Quick Search</h2>
        </div>
        <div className="flex gap-2">
          <a
            className="flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-9 px-4 bg-[#f0f2f4] hover:bg-[#e4e7eb] text-text-primary text-sm font-bold leading-normal tracking-[0.015em] transition-colors"
            href="mailto:emong111@naver.com"
          >
            <span className="truncate">Contact Support</span>
          </a>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center py-12 px-4 sm:px-6">
        <div className="w-full max-w-[440px] flex flex-col">
          {/* Headline Section */}
          <div className="text-center mb-10">
            <h1 className="text-text-primary tracking-tight text-[32px] font-bold leading-tight mb-3">Create Account</h1>
            <p className="text-text-secondary text-base font-normal leading-normal">
              Sign up to access document search features.
            </p>
          </div>

          {/* Divider */}
          <div className="relative flex items-center py-2 mb-8">
            <div className="flex-grow border-t border-[#e5e7eb]"></div>
            <span className="flex-shrink-0 mx-4 text-[#9ca3af] text-sm font-medium">PDF Quick Search</span>
            <div className="flex-grow border-t border-[#e5e7eb]"></div>
          </div>

          {/* Signup Form */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            {/* Email Field */}
            <div className="flex flex-col gap-2">
              <label className="text-text-primary text-sm font-medium leading-normal" htmlFor="email">
                Email address
              </label>
              <input
                className={`flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-text-primary focus:outline-0 focus:ring-2 focus:ring-primary/20 border ${errors.email ? 'border-red-400' : 'border-[#dbe0e6]'} bg-white focus:border-primary h-12 placeholder:text-[#9ca3af] p-[15px] text-base font-normal leading-normal transition-colors`}
                id="email"
                name="email"
                placeholder="이메일"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                autoComplete="email"
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email}</p>
              )}
            </div>

            {/* Name Field */}
            <div className="flex flex-col gap-2">
              <label className="text-text-primary text-sm font-medium leading-normal" htmlFor="name">
                Name
              </label>
              <input
                className={`flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-text-primary focus:outline-0 focus:ring-2 focus:ring-primary/20 border ${errors.name ? 'border-red-400' : 'border-[#dbe0e6]'} bg-white focus:border-primary h-12 placeholder:text-[#9ca3af] p-[15px] text-base font-normal leading-normal transition-colors`}
                id="name"
                name="name"
                placeholder="이름"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={isLoading}
                autoComplete="name"
              />
              {errors.name && (
                <p className="text-sm text-red-500">{errors.name}</p>
              )}
            </div>

            {/* Phone Field */}
            <div className="flex flex-col gap-2">
              <label className="text-text-primary text-sm font-medium leading-normal" htmlFor="phone">
                Phone
              </label>
              <input
                className={`flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-text-primary focus:outline-0 focus:ring-2 focus:ring-primary/20 border ${errors.phone ? 'border-red-400' : 'border-[#dbe0e6]'} bg-white focus:border-primary h-12 placeholder:text-[#9ca3af] p-[15px] text-base font-normal leading-normal transition-colors`}
                id="phone"
                name="phone"
                placeholder="휴대폰번호 (010-1234-5678)"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                disabled={isLoading}
                autoComplete="tel"
              />
              {errors.phone && (
                <p className="text-sm text-red-500">{errors.phone}</p>
              )}
            </div>

            {/* Password Field */}
            <div className="flex flex-col gap-2">
              <label className="text-text-primary text-sm font-medium leading-normal" htmlFor="password">
                Password
              </label>
              <div className="relative flex w-full items-center rounded-lg">
                <input
                  className={`flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-text-primary focus:outline-0 focus:ring-2 focus:ring-primary/20 border ${errors.password ? 'border-red-400' : 'border-[#dbe0e6]'} bg-white focus:border-primary h-12 placeholder:text-[#9ca3af] p-[15px] pr-12 text-base font-normal leading-normal transition-colors`}
                  id="password"
                  name="password"
                  placeholder="비밀번호"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                  autoComplete="new-password"
                />
                <button
                  className="absolute right-0 top-0 bottom-0 flex items-center justify-center px-4 cursor-pointer text-[#9ca3af] hover:text-text-primary transition-colors focus:outline-none"
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  <span className="material-symbols-outlined text-[20px]">
                    {showPassword ? 'visibility_off' : 'visibility'}
                  </span>
                </button>
              </div>
              {errors.password && (
                <p className="text-sm text-red-500">{errors.password}</p>
              )}
              <p className="text-xs text-text-secondary">
                8자 이상, 대문자, 소문자, 숫자 포함
              </p>
            </div>

            {/* Password Confirm Field */}
            <div className="flex flex-col gap-2">
              <label className="text-text-primary text-sm font-medium leading-normal" htmlFor="passwordConfirm">
                Confirm Password
              </label>
              <div className="relative flex w-full items-center rounded-lg">
                <input
                  className={`flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-text-primary focus:outline-0 focus:ring-2 focus:ring-primary/20 border ${errors.passwordConfirm ? 'border-red-400' : 'border-[#dbe0e6]'} bg-white focus:border-primary h-12 placeholder:text-[#9ca3af] p-[15px] pr-12 text-base font-normal leading-normal transition-colors`}
                  id="passwordConfirm"
                  name="passwordConfirm"
                  placeholder="비밀번호 확인"
                  type={showPasswordConfirm ? 'text' : 'password'}
                  value={passwordConfirm}
                  onChange={(e) => setPasswordConfirm(e.target.value)}
                  disabled={isLoading}
                  autoComplete="new-password"
                />
                <button
                  className="absolute right-0 top-0 bottom-0 flex items-center justify-center px-4 cursor-pointer text-[#9ca3af] hover:text-text-primary transition-colors focus:outline-none"
                  type="button"
                  onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                >
                  <span className="material-symbols-outlined text-[20px]">
                    {showPasswordConfirm ? 'visibility_off' : 'visibility'}
                  </span>
                </button>
              </div>
              {errors.passwordConfirm && (
                <p className="text-sm text-red-500">{errors.passwordConfirm}</p>
              )}
            </div>

            {/* Server Error Message */}
            {serverError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{serverError}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              className="mt-4 flex w-full cursor-pointer items-center justify-center overflow-hidden rounded-lg h-12 px-4 bg-primary hover:bg-blue-600 text-white text-sm font-bold leading-normal tracking-[0.015em] shadow-sm transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
              type="submit"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="material-symbols-outlined text-[20px] animate-spin">progress_activity</span>
              ) : (
                <span className="truncate">Sign Up</span>
              )}
            </button>
          </form>

          {/* Login Link */}
          <div className="mt-8 text-center">
            <p className="text-text-secondary text-sm">
              Already have an account?{' '}
              <Link to="/login" className="text-primary hover:text-blue-600 font-medium transition-colors">
                Log in
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
