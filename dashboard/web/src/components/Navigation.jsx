import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Sparkles, 
  Users, 
  MessageSquare, 
  Database,
  FlaskConical,
  RefreshCw
} from 'lucide-react';
import { COLORS } from '../App';
import { useApiData } from '../hooks/useApiData';

const navItems = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/adoption', label: 'Adoption', icon: Users },
  { path: '/feedback', label: 'Feedback', icon: MessageSquare },
  { path: '/query-rewriter', label: 'Query Rewriter', icon: Sparkles },
  { path: '/content-health', label: 'Content Health', icon: Database },
];

const Navigation = () => {
  const location = useLocation();
  const { lastUpdated, isSyncing, triggerSync } = useApiData();
  
  // Get current page for breadcrumb
  const currentPage = navItems.find(item => item.path === location.pathname);
  
  // Format last updated time
  const formatLastUpdated = (date) => {
    if (!date) return 'Never';
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return date.toLocaleTimeString();
  };
  
  return (
    <nav 
      className="sticky top-0 z-50 border-b border-white/10"
      style={{ background: COLORS.surface }}
    >
      <div className="max-w-7xl mx-auto px-6">
        {/* Top Bar: Logo + Title */}
        <div className="flex items-center justify-between py-4 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div 
              className="p-2 rounded-lg"
              style={{ background: 'rgba(124, 58, 237, 0.2)' }}
            >
              <FlaskConical size={24} style={{ color: COLORS.purple }} />
            </div>
            <div>
              <h1 className="text-lg font-bold" style={{ color: COLORS.textPrimary }}>
                Nexus IQ <span className="text-xs font-normal opacity-50">v2</span>
              </h1>
              <p className="text-xs" style={{ color: COLORS.textMuted }}>
                Query Optimizer Observability
              </p>
            </div>
          </div>
          
          {/* Right side: Last updated + Refresh button */}
          <div className="flex items-center gap-4">
            {/* Last Updated */}
            <div className="text-xs" style={{ color: COLORS.textMuted }}>
              Updated: {formatLastUpdated(lastUpdated)}
            </div>
            
            {/* Refresh Button */}
            <button
              onClick={() => triggerSync(false)}
              disabled={isSyncing}
              className={`
                flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium
                transition-all duration-200 border
                ${isSyncing 
                  ? 'opacity-50 cursor-not-allowed' 
                  : 'hover:bg-white/10 active:scale-95'
                }
              `}
              style={{ 
                borderColor: 'rgba(124, 58, 237, 0.3)',
                color: COLORS.purple,
              }}
            >
              <RefreshCw 
                size={14} 
                className={isSyncing ? 'animate-spin' : ''} 
              />
              {isSyncing ? 'Syncing...' : 'Refresh'}
            </button>
            
            {/* Breadcrumb */}
            <div className="flex items-center gap-2 text-sm pl-4 border-l border-white/10">
              <span style={{ color: COLORS.textMuted }}>Dashboard</span>
              <span style={{ color: COLORS.textMuted }}>/</span>
              <span style={{ color: COLORS.purple }}>{currentPage?.label || 'Overview'}</span>
            </div>
          </div>
        </div>
        
        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 py-2 overflow-x-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`
                  flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium
                  transition-all duration-200 whitespace-nowrap
                  ${isActive 
                    ? 'bg-white/10' 
                    : 'hover:bg-white/5'
                  }
                `}
                style={{ 
                  color: isActive ? COLORS.purple : COLORS.textMuted,
                }}
              >
                <Icon size={16} />
                {item.label}
              </NavLink>
            );
          })}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
