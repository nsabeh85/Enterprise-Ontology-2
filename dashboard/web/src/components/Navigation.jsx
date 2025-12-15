import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Sparkles, 
  Users, 
  MessageSquare, 
  Database,
  FlaskConical
} from 'lucide-react';
import { COLORS } from '../App';

const navItems = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/adoption', label: 'Adoption', icon: Users },
  { path: '/feedback', label: 'Feedback', icon: MessageSquare },
  { path: '/query-rewriter', label: 'Query Rewriter', icon: Sparkles },
  { path: '/content-health', label: 'Content Health', icon: Database },
];

const Navigation = () => {
  const location = useLocation();
  
  // Get current page for breadcrumb
  const currentPage = navItems.find(item => item.path === location.pathname);
  
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
                Nexus IQ
              </h1>
              <p className="text-xs" style={{ color: COLORS.textMuted }}>
                Query Optimizer Observability
              </p>
            </div>
          </div>
          
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-sm">
            <span style={{ color: COLORS.textMuted }}>Dashboard</span>
            <span style={{ color: COLORS.textMuted }}>/</span>
            <span style={{ color: COLORS.purple }}>{currentPage?.label || 'Overview'}</span>
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
