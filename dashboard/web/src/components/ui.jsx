import React, { useState } from 'react';
import { Info, TrendingUp, AlertTriangle } from 'lucide-react';
import { COLORS } from '../App';

// Info Tooltip Component
export const InfoTooltip = ({ text }) => {
  const [isVisible, setIsVisible] = useState(false);
  
  return (
    <div className="relative inline-flex items-center">
      <button
        className="p-1 rounded-full transition-colors hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-white/20"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        aria-label="More information"
      >
        <Info size={14} style={{ color: COLORS.textMuted }} />
      </button>
      {isVisible && (
        <div 
          className="absolute z-50 left-1/2 -translate-x-1/2 bottom-full mb-2 pointer-events-none"
          style={{ minWidth: '280px', maxWidth: '280px' }}
        >
          <div
            className="px-3 py-2 rounded-md text-xs leading-relaxed"
            style={{
              background: 'rgba(0, 0, 0, 0.9)',
              color: '#fafafa',
              fontSize: '12px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
            }}
          >
            {text}
          </div>
          <div
            className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0"
            style={{
              borderLeft: '6px solid transparent',
              borderRight: '6px solid transparent',
              borderTop: '6px solid rgba(0, 0, 0, 0.9)',
            }}
          />
        </div>
      )}
    </div>
  );
};

// Title with Info Component
export const TitleWithInfo = ({ children, tooltip, className = '' }) => (
  <div className={`flex items-center gap-2 ${className}`}>
    <h3 className="text-xl font-semibold" style={{ color: COLORS.textPrimary }}>
      {children}
    </h3>
    {tooltip && <InfoTooltip text={tooltip} />}
  </div>
);

// Card Component
export const Card = ({ children, className = '', delay = 0 }) => (
  <div
    className={`px-6 py-6 rounded-lg border border-white/10 opacity-0 animate-fade-in-up ${className}`}
    style={{
      background: COLORS.surface,
      boxShadow: '0 4px 24px rgba(0, 0, 0, 0.2)',
      animationDelay: `${delay}ms`,
      animationFillMode: 'forwards',
    }}
  >
    {children}
  </div>
);

// KPI Card Component
export const KPICard = ({ title, value, subtitle, icon: Icon, trend, trendLabel, delay = 0, tooltip }) => (
  <Card delay={delay}>
    <div className="flex items-start justify-between">
      <div>
        <div className="flex items-center gap-1.5">
          <p className="text-sm font-medium" style={{ color: COLORS.textMuted }}>{title}</p>
          {tooltip && <InfoTooltip text={tooltip} />}
        </div>
        <p className="text-4xl font-extrabold tracking-tight mt-2" style={{ color: COLORS.textPrimary }}>
          {value}
        </p>
        {subtitle && (
          <p className="text-sm mt-1" style={{ color: COLORS.textMuted }}>{subtitle}</p>
        )}
        {trend && (
          <div className="mt-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
            style={{ 
              background: trend === 'positive' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              color: trend === 'positive' ? '#22c55e' : '#ef4444',
            }}>
            {trend === 'positive' ? <TrendingUp size={12} /> : <AlertTriangle size={12} />}
            {trendLabel}
          </div>
        )}
      </div>
      {Icon && (
        <div className="p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.05)' }}>
          <Icon size={24} style={{ color: COLORS.purple }} />
        </div>
      )}
    </div>
  </Card>
);

// Badge Component
export const Badge = ({ children, variant = 'default' }) => {
  const variants = {
    default: { bg: 'rgba(255,255,255,0.1)', color: COLORS.textPrimary },
    success: { bg: 'rgba(34, 197, 94, 0.15)', color: '#22c55e' },
    warning: { bg: 'rgba(234, 179, 8, 0.15)', color: '#eab308' },
    danger: { bg: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' },
    info: { bg: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6' },
  };
  
  return (
    <span 
      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium"
      style={variants[variant]}
    >
      {children}
    </span>
  );
};

// Score Bar Component
export const ScoreBar = ({ score, maxScore = 5, color }) => {
  const percentage = (score / maxScore) * 100;
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.1)' }}>
        <div 
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${percentage}%`, background: color }}
        />
      </div>
      <span className="text-sm font-bold w-10 text-right" style={{ color }}>{score}</span>
    </div>
  );
};

// Custom Chart Tooltip
export const CustomChartTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="px-4 py-3 rounded-lg border border-white/10" style={{ background: COLORS.surface }}>
        <p className="text-sm font-medium" style={{ color: COLORS.textPrimary }}>{label}</p>
        {payload.map((entry, index) => (
          <p key={index} className="text-sm" style={{ color: entry.color || COLORS.textMuted }}>
            {entry.name}: {entry.value}{entry.unit || ''}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Page Header Component
export const PageHeader = ({ title, subtitle, icon: Icon, badge }) => (
  <header className="mb-8 opacity-0 animate-fade-in-up" style={{ animationFillMode: 'forwards' }}>
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        {Icon && (
          <div 
            className="p-3 rounded-lg"
            style={{ background: 'rgba(124, 58, 237, 0.2)' }}
          >
            <Icon size={28} style={{ color: COLORS.purple }} />
          </div>
        )}
        <div>
          <h1 className="text-3xl font-bold" style={{ color: COLORS.textPrimary }}>
            {title}
          </h1>
          {subtitle && (
            <p className="text-sm mt-1" style={{ color: COLORS.textMuted }}>
              {subtitle}
            </p>
          )}
        </div>
      </div>
      {badge}
    </div>
  </header>
);
