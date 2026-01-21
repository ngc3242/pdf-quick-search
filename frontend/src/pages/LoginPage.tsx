import { useState, type FormEvent } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore } from '@/store';

type ErrorType = 'default' | 'pending' | 'rejected';

function getErrorType(error: string): ErrorType {
  if (error.includes('승인 대기')) {
    return 'pending';
  }
  if (error.includes('거부')) {
    return 'rejected';
  }
  return 'default';
}

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  const { login, isLoading } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/';

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('이메일과 비밀번호를 입력해주세요');
      return;
    }

    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '이메일 또는 비밀번호가 올바르지 않습니다';
      setError(errorMessage);
    }
  };

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
            <span className="truncate">문의하기</span>
          </a>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center py-12 px-4 sm:px-6">
        <div className="w-full max-w-[440px] flex flex-col">
          {/* Headline Section */}
          <div className="text-center mb-10">
            <h1 className="text-text-primary tracking-tight text-[32px] font-bold leading-tight mb-3">다시 오신 것을 환영합니다</h1>
            <p className="text-text-secondary text-base font-normal leading-normal">
              문서에 접근하고 검색을 시작하려면 로그인하세요.
            </p>
          </div>

          {/* Divider */}
          <div className="relative flex items-center py-2 mb-8">
            <div className="flex-grow border-t border-[#e5e7eb]"></div>
            <span className="flex-shrink-0 mx-4 text-[#9ca3af] text-sm font-medium">PDF Quick Search</span>
            <div className="flex-grow border-t border-[#e5e7eb]"></div>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            {/* Email Field */}
            <div className="flex flex-col gap-2">
              <label className="text-text-primary text-sm font-medium leading-normal" htmlFor="email">
                이메일 주소
              </label>
              <input
                className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-text-primary focus:outline-0 focus:ring-2 focus:ring-primary/20 border border-[#dbe0e6] bg-white focus:border-primary h-12 placeholder:text-[#9ca3af] p-[15px] text-base font-normal leading-normal transition-colors"
                id="email"
                name="email"
                placeholder="name@company.com"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                autoComplete="email"
              />
            </div>

            {/* Password Field */}
            <div className="flex flex-col gap-2">
              <div className="flex justify-between items-center">
                <label className="text-text-primary text-sm font-medium leading-normal" htmlFor="password">
                  비밀번호
                </label>
              </div>
              <div className="relative flex w-full items-center rounded-lg">
                <input
                  className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-text-primary focus:outline-0 focus:ring-2 focus:ring-primary/20 border border-[#dbe0e6] bg-white focus:border-primary h-12 placeholder:text-[#9ca3af] p-[15px] pr-12 text-base font-normal leading-normal transition-colors"
                  id="password"
                  name="password"
                  placeholder="비밀번호를 입력하세요"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                  autoComplete="current-password"
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
            </div>

            {/* Error Message */}
            {error && (() => {
              const errorType = getErrorType(error);

              if (errorType === 'pending') {
                return (
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                    <div className="flex items-start gap-3">
                      <span className="material-symbols-outlined text-amber-600 text-[20px] mt-0.5">hourglass_empty</span>
                      <div>
                        <p className="text-sm font-medium text-amber-800">{error}</p>
                        <p className="text-sm text-amber-700 mt-1">관리자 승인 후 로그인이 가능합니다.</p>
                      </div>
                    </div>
                  </div>
                );
              }

              if (errorType === 'rejected') {
                return (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-start gap-3">
                      <span className="material-symbols-outlined text-red-600 text-[20px] mt-0.5">cancel</span>
                      <div>
                        <p className="text-sm font-medium text-red-800">{error}</p>
                        <p className="text-sm text-red-700 mt-1">관리자에게 문의하세요.</p>
                      </div>
                    </div>
                  </div>
                );
              }

              return (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              );
            })()}

            {/* Submit Button */}
            <button
              className="mt-4 flex w-full cursor-pointer items-center justify-center overflow-hidden rounded-lg h-12 px-4 bg-primary hover:bg-blue-600 text-white text-sm font-bold leading-normal tracking-[0.015em] shadow-sm transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
              type="submit"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="material-symbols-outlined text-[20px] animate-spin">progress_activity</span>
              ) : (
                <span className="truncate">로그인</span>
              )}
            </button>
          </form>

          {/* Sign Up Link */}
          <div className="mt-8 text-center">
            <p className="text-text-secondary text-sm">
              계정이 없으신가요?{' '}
              <Link
                to="/signup"
                className="text-primary hover:text-blue-600 font-medium transition-colors"
              >
                회원가입
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
