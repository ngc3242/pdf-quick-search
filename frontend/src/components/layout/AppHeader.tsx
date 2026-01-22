import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

interface AppHeaderProps {
  showGlobalSearch?: boolean;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  onSearch?: (query: string) => void;
  onClearSearch?: () => void;
  isSearching?: boolean;
}

export function AppHeader({
  showGlobalSearch = false,
  searchQuery = '',
  onSearchChange,
  onSearch,
  onClearSearch,
  isSearching = false,
}: AppHeaderProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const isAdmin = user?.role === 'admin';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && onSearch) {
      onSearch(searchQuery);
    }
    if (e.key === 'Escape' && onClearSearch) {
      onClearSearch();
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-[#e5e7eb] shadow-sm">
      <div className="flex items-center justify-between h-16 px-4 lg:px-10 max-w-[1400px] mx-auto w-full">
        {/* Logo - clickable to home */}
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-3 hover:opacity-80 transition-opacity"
        >
          <div className="size-10 rounded-lg bg-primary flex items-center justify-center text-white shadow-sm">
            <span className="material-symbols-outlined text-2xl">picture_as_pdf</span>
          </div>
          <h2 className="text-text-primary text-lg font-bold leading-tight tracking-[-0.015em] hidden sm:block">
            PDF Quick Search
          </h2>
        </button>

        {/* Global Search (Full-text) - Only shown when enabled */}
        {showGlobalSearch && (
          <div className="hidden md:flex flex-1 max-w-[480px] px-8">
            <label className="flex flex-col w-full !h-10">
              <div className="flex w-full flex-1 items-stretch rounded-lg h-full ring-1 ring-[#dbe0e6] focus-within:ring-2 focus-within:ring-primary overflow-hidden">
                <div className="text-text-secondary flex border-none bg-[#f9fafb] items-center justify-center pl-4 rounded-l-lg border-r-0">
                  {isSearching ? (
                    <span className="material-symbols-outlined text-[20px] text-primary animate-spin">
                      progress_activity
                    </span>
                  ) : (
                    <span className="material-symbols-outlined text-[20px]">search</span>
                  )}
                </div>
                <input
                  className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg rounded-l-none text-text-primary focus:outline-0 border-none bg-[#f9fafb] h-full placeholder:text-text-secondary px-3 text-sm font-normal leading-normal"
                  placeholder="전문 검색 (문서 내용에서 검색)..."
                  value={searchQuery}
                  onChange={(e) => onSearchChange?.(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
                {searchQuery && (
                  <button
                    onClick={onClearSearch}
                    className="flex items-center justify-center px-3 text-text-secondary hover:text-text-primary transition-colors"
                  >
                    <span className="material-symbols-outlined text-[20px]">close</span>
                  </button>
                )}
              </div>
            </label>
          </div>
        )}

        <div className="flex items-center justify-end gap-4 lg:gap-8">
          {/* Admin link */}
          {isAdmin && (
            <nav className="hidden lg:flex items-center">
              <button
                onClick={() => navigate('/admin')}
                className="text-text-primary text-sm font-medium hover:text-primary transition-colors"
              >
                Users
              </button>
            </nav>
          )}

          {/* Logout button */}
          <button
            onClick={handleLogout}
            className="flex items-center justify-center rounded-full size-10 hover:bg-[#f0f2f4] transition-colors text-text-primary"
            title="로그아웃"
          >
            <span className="material-symbols-outlined">logout</span>
          </button>

          {/* User avatar */}
          <div className="bg-primary text-white rounded-full size-10 flex items-center justify-center text-sm font-bold cursor-pointer">
            {user?.name?.charAt(0).toUpperCase() || 'U'}
          </div>
        </div>
      </div>
    </header>
  );
}
