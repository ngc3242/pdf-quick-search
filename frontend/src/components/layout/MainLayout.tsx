import { AppHeader } from './AppHeader';
import { FeatureTabBar } from './FeatureTabBar';

interface MainLayoutProps {
  children: React.ReactNode;
  showGlobalSearch?: boolean;
  searchProps?: {
    query: string;
    onQueryChange: (query: string) => void;
    onSearch: (query: string) => void;
    onClearSearch: () => void;
    isSearching: boolean;
  };
}

export function MainLayout({
  children,
  showGlobalSearch = false,
  searchProps,
}: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-background-light flex flex-col">
      <AppHeader
        showGlobalSearch={showGlobalSearch}
        searchQuery={searchProps?.query}
        onSearchChange={searchProps?.onQueryChange}
        onSearch={searchProps?.onSearch}
        onClearSearch={searchProps?.onClearSearch}
        isSearching={searchProps?.isSearching}
      />
      <FeatureTabBar />
      <main className="flex-1">{children}</main>
    </div>
  );
}
