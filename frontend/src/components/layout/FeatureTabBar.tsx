import { useLocation, useNavigate } from 'react-router-dom';

interface SubTab {
  id: string;
  label: string;
  path: string;
  icon: string;
}

interface FeatureTab {
  id: string;
  label: string;
  path: string;
  icon: string;
  subPaths: string[];
  subTabs?: SubTab[];
}

const FEATURE_TABS: FeatureTab[] = [
  {
    id: 'pdf-search',
    label: 'PDF 검색',
    path: '/',
    icon: 'search',
    subPaths: ['/', '/documents'],
    subTabs: [
      { id: 'search', label: '검색', path: '/', icon: 'search' },
      { id: 'documents', label: '문서 관리', path: '/documents', icon: 'folder_open' },
    ],
  },
  {
    id: 'spell-checker',
    label: '맞춤법 검사',
    path: '/typo-checker',
    icon: 'spellcheck',
    subPaths: ['/typo-checker'],
  },
];

export function FeatureTabBar() {
  const location = useLocation();
  const navigate = useNavigate();

  const isTabActive = (tab: FeatureTab) => {
    return tab.subPaths.includes(location.pathname);
  };

  const activeTab = FEATURE_TABS.find((tab) => isTabActive(tab));
  const showSubTabs = activeTab?.subTabs && activeTab.subTabs.length > 0;

  return (
    <div className="bg-white border-b border-[#e5e7eb]">
      <div className="max-w-[1400px] mx-auto px-4 lg:px-10">
        {/* Main Feature Tabs */}
        <nav className="flex">
          {FEATURE_TABS.map((tab) => {
            const active = isTabActive(tab);
            return (
              <button
                key={tab.id}
                onClick={() => navigate(tab.path)}
                className={`relative flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors ${
                  active
                    ? 'text-primary'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                <span
                  className="material-symbols-outlined text-[20px]"
                  style={{
                    fontVariationSettings: active ? "'FILL' 1" : "'FILL' 0",
                  }}
                >
                  {tab.icon}
                </span>
                <span>{tab.label}</span>
                {active && !showSubTabs && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Sub Tabs for PDF Search */}
      {showSubTabs && activeTab?.subTabs && (
        <div className="bg-gray-50 border-b border-[#e5e7eb]">
          <div className="max-w-[1400px] mx-auto px-4 lg:px-10">
            <nav className="flex gap-1">
              {activeTab.subTabs.map((subTab) => {
                const isSubActive = location.pathname === subTab.path;
                return (
                  <button
                    key={subTab.id}
                    onClick={() => navigate(subTab.path)}
                    className={`relative flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors ${
                      isSubActive
                        ? 'bg-white text-primary border-t border-l border-r border-[#e5e7eb] -mb-px'
                        : 'text-text-secondary hover:text-text-primary hover:bg-gray-100'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      {subTab.icon}
                    </span>
                    <span>{subTab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>
      )}
    </div>
  );
}
