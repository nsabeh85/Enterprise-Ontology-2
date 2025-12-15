import React, { useMemo } from 'react';
import { 
  LayoutDashboard, 
  Sparkles, 
  Users, 
  ThumbsUp, 
  Target,
  Clock,
  FileSearch,
  CheckCircle,
  AlertCircle,
  ChevronRight
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { COLORS } from '../App';
import { Card, Badge, PageHeader } from '../components/ui';

// Import data
import { useApiData } from '../hooks/useApiData';

// =============================================================================
// OBSERVABILITY SCORE CALCULATIONS
// =============================================================================

const calculateQueryPerformanceScore = (rewriterData) => {
  const { summary, latencyStats, qualityScores } = rewriterData;
  
  const latency = latencyStats?.avg || 0;
  const latencyScore = Math.max(0, Math.min(100, 100 - (latency - 10) * (100 / 90)));
  
  const matchRate = summary?.rewriteRate || 0;
  
  const rewrittenScores = qualityScores?.rewritten || {};
  const avgQuality = (
    (rewrittenScores.relevance || 0) + 
    (rewrittenScores.groundedness || 0) + 
    (rewrittenScores.completeness || 0)
  ) / 3;
  const qualityScore = (avgQuality / 5) * 100;
  
  const overall = (latencyScore * 0.4) + (matchRate * 0.3) + (qualityScore * 0.3);
  
  return {
    overall: Math.round(overall),
    breakdown: {
      latency: `${latency.toFixed(1)}ms`,
      matchRate: `${matchRate.toFixed(1)}%`,
      quality: avgQuality.toFixed(1)
    }
  };
};

const calculateUserAdoptionScore = (adoptionData, feedbackData) => {
  const stickiness = adoptionData?.stickiness || 0;
  const stickinessScore = Math.min(100, (stickiness / 50) * 100);
  
  const positiveRate = feedbackData?.summary?.positiveRate || 0;
  
  const wau = adoptionData?.wau || 0;
  const wauScore = Math.min(100, (wau / 150) * 100);
  
  const overall = (stickinessScore * 0.4) + (positiveRate * 0.3) + (wauScore * 0.3);
  
  return {
    overall: Math.round(overall),
    breakdown: {
      wau: adoptionData?.wau || 0,
      stickiness: `${stickiness.toFixed(1)}%`,
      positiveRate: `${positiveRate.toFixed(1)}%`
    }
  };
};

const calculateContentHealthScore = (rewriterData) => {
  const zeroResultRate = rewriterData?.summary?.zeroResultRate || 0;
  const overall = Math.round(100 - zeroResultRate);
  
  return {
    overall,
    breakdown: {
      zeroResultRate: `${zeroResultRate.toFixed(1)}%`,
      totalQueries: rewriterData?.summary?.totalQueries || 0
    }
  };
};

// =============================================================================
// OBSERVABILITY COMPONENTS
// =============================================================================

const ScoreRing = ({ score, size = 90, strokeWidth = 7, color }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;
  
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xl font-bold" style={{ color: COLORS.textPrimary }}>
          {score}%
        </span>
      </div>
    </div>
  );
};

const ObservabilityCard = ({ title, score, icon: Icon, color, breakdown, linkTo, delay = 0 }) => {
  const navigate = useNavigate();
  
  const getStatus = (score) => {
    if (score >= 70) return { label: 'Healthy', color: COLORS.green };
    if (score >= 50) return { label: 'Needs Attention', color: '#EAB308' };
    return { label: 'Action Required', color: COLORS.red };
  };
  
  const status = getStatus(score);
  
  return (
    <Card delay={delay}>
      <div className="flex flex-col h-full">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-2 rounded-lg" style={{ background: `${color}20` }}>
            <Icon size={18} style={{ color }} />
          </div>
          <div>
            <h3 className="font-semibold text-sm" style={{ color: COLORS.textPrimary }}>{title}</h3>
            <p className="text-xs" style={{ color: status.color }}>{status.label}</p>
          </div>
        </div>
        
        <div className="flex justify-center mb-3">
          <ScoreRing score={score} color={color} />
        </div>
        
        <div className="space-y-1 mb-3 flex-1">
          {Object.entries(breakdown).map(([key, value]) => (
            <div key={key} className="flex justify-between items-center">
              <span className="text-xs capitalize" style={{ color: COLORS.textMuted }}>
                {key.replace(/([A-Z])/g, ' $1').trim()}
              </span>
              <span className="text-xs font-medium" style={{ color: COLORS.textPrimary }}>{value}</span>
            </div>
          ))}
        </div>
        
        <button
          onClick={() => navigate(linkTo)}
          className="flex items-center justify-center gap-1 w-full py-2 rounded-lg transition-all hover:opacity-80"
          style={{ background: `${color}15`, color: color }}
        >
          <span className="text-xs font-medium">View Details</span>
          <ChevronRight size={14} />
        </button>
      </div>
    </Card>
  );
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

const Overview = () => {
  // Fetch live data
  const { data, loading, error, lastUpdated } = useApiData();
  
  // Use API data (with fallbacks) - must be before any conditional returns
  const rewriterData = data?.rewriter || {};
  const adoptionData = data?.adoption || {};
  const feedbackData = data?.feedback || {};
  
  const { summary } = rewriterData;

  // Calculate observability scores - useMemo must be called before any early returns
  const queryPerformance = useMemo(
    () => calculateQueryPerformanceScore(rewriterData), 
    [rewriterData]
  );
  const userAdoption = useMemo(
    () => calculateUserAdoptionScore(adoptionData, feedbackData), 
    [adoptionData, feedbackData]
  );
  const contentHealth = useMemo(
    () => calculateContentHealthScore(rewriterData), 
    [rewriterData]
  );

  // Overall system health
  const overallHealth = useMemo(() => {
    const avgScore = (queryPerformance.overall + userAdoption.overall + contentHealth.overall) / 3;
    if (avgScore >= 70) return { label: 'All Systems Healthy', icon: CheckCircle, color: COLORS.green };
    if (avgScore >= 50) return { label: 'Needs Attention', icon: AlertCircle, color: '#EAB308' };
    return { label: 'Action Required', icon: AlertCircle, color: COLORS.red };
  }, [queryPerformance, userAdoption, contentHealth]);

  // Loading state - AFTER all hooks are called
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p style={{ color: COLORS.textMuted }}>Loading dashboard...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-8">
      <PageHeader 
        title="Dashboard Overview"
        subtitle="Key metrics across all Nexus analytics"
        icon={LayoutDashboard}
        badge={
          <Badge>
            <Clock size={12} />
            Updated: {new Date().toLocaleDateString()}
          </Badge>
        }
      />

      {/* ================================================================== */}
      {/* OBSERVABILITY SECTION */}
      {/* ================================================================== */}
      
      {/* System Health Banner */}
      <Card delay={50}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl" style={{ background: `${overallHealth.color}20` }}>
              <overallHealth.icon size={24} style={{ color: overallHealth.color }} />
            </div>
            <div>
              <p className="text-sm" style={{ color: COLORS.textMuted }}>System Status</p>
              <p className="text-xl font-bold" style={{ color: overallHealth.color }}>
                {overallHealth.label}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="text-center">
              <p className="text-xl font-bold" style={{ color: COLORS.purple }}>{queryPerformance.overall}%</p>
              <p className="text-xs" style={{ color: COLORS.textMuted }}>Performance</p>
            </div>
            <div className="text-center">
              <p className="text-xl font-bold" style={{ color: COLORS.cyan }}>{userAdoption.overall}%</p>
              <p className="text-xs" style={{ color: COLORS.textMuted }}>Adoption</p>
            </div>
            <div className="text-center">
              <p className="text-xl font-bold" style={{ color: COLORS.green }}>{contentHealth.overall}%</p>
              <p className="text-xs" style={{ color: COLORS.textMuted }}>Content</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Three Observability Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <ObservabilityCard
          title="Query Performance"
          score={queryPerformance.overall}
          icon={Sparkles}
          color={COLORS.purple}
          breakdown={queryPerformance.breakdown}
          linkTo="/query-rewriter"
          delay={100}
        />
        
        <ObservabilityCard
          title="User Adoption"
          score={userAdoption.overall}
          icon={Users}
          color={COLORS.cyan}
          breakdown={userAdoption.breakdown}
          linkTo="/adoption"
          delay={150}
        />
        
        <ObservabilityCard
          title="Content Health"
          score={contentHealth.overall}
          icon={FileSearch}
          color={COLORS.green}
          breakdown={contentHealth.breakdown}
          linkTo="/content-health"
          delay={200}
        />
      </div>

      {/* ================================================================== */}
      {/* ANSWER QUALITY SCORES */}
      {/* ================================================================== */}
      
      <Card delay={250}>
        <div className="flex items-center gap-2 mb-4">
          <Target size={20} style={{ color: COLORS.orange }} />
          <h3 className="font-semibold" style={{ color: COLORS.textPrimary }}>Answer Quality Scores</h3>
          <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'rgba(255,255,255,0.1)', color: COLORS.textMuted }}>
            LLM-as-Judge
          </span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Relevance */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium" style={{ color: COLORS.textPrimary }}>Relevance</span>
              <span className="text-xs" style={{ color: COLORS.textMuted }}>/ 5.0</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-xs w-20" style={{ color: COLORS.textMuted }}>Rewritten</span>
                <div className="flex-1 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.1)' }}>
                  <div 
                    className="h-full rounded-full" 
                    style={{ 
                      width: `${((rewriterData.qualityScores?.rewritten?.relevance || 0) / 5) * 100}%`,
                      background: COLORS.purple 
                    }} 
                  />
                </div>
                <span className="text-sm font-bold w-8" style={{ color: COLORS.purple }}>
                  {rewriterData.qualityScores?.rewritten?.relevance?.toFixed(1) || '0.0'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs w-20" style={{ color: COLORS.textMuted }}>Passthrough</span>
                <div className="flex-1 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.1)' }}>
                  <div 
                    className="h-full rounded-full" 
                    style={{ 
                      width: `${((rewriterData.qualityScores?.passthrough?.relevance || 0) / 5) * 100}%`,
                      background: COLORS.orange 
                    }} 
                  />
                </div>
                <span className="text-sm font-bold w-8" style={{ color: COLORS.orange }}>
                  {rewriterData.qualityScores?.passthrough?.relevance?.toFixed(1) || '0.0'}
                </span>
              </div>
            </div>
          </div>
          
          {/* Groundedness */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium" style={{ color: COLORS.textPrimary }}>Groundedness</span>
              <span className="text-xs" style={{ color: COLORS.textMuted }}>/ 5.0</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-xs w-20" style={{ color: COLORS.textMuted }}>Rewritten</span>
                <div className="flex-1 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.1)' }}>
                  <div 
                    className="h-full rounded-full" 
                    style={{ 
                      width: `${((rewriterData.qualityScores?.rewritten?.groundedness || 0) / 5) * 100}%`,
                      background: COLORS.purple 
                    }} 
                  />
                </div>
                <span className="text-sm font-bold w-8" style={{ color: COLORS.purple }}>
                  {rewriterData.qualityScores?.rewritten?.groundedness?.toFixed(1) || '0.0'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs w-20" style={{ color: COLORS.textMuted }}>Passthrough</span>
                <div className="flex-1 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.1)' }}>
                  <div 
                    className="h-full rounded-full" 
                    style={{ 
                      width: `${((rewriterData.qualityScores?.passthrough?.groundedness || 0) / 5) * 100}%`,
                      background: COLORS.orange 
                    }} 
                  />
                </div>
                <span className="text-sm font-bold w-8" style={{ color: COLORS.orange }}>
                  {rewriterData.qualityScores?.passthrough?.groundedness?.toFixed(1) || '0.0'}
                </span>
              </div>
            </div>
          </div>
          
          {/* Completeness */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium" style={{ color: COLORS.textPrimary }}>Completeness</span>
              <span className="text-xs" style={{ color: COLORS.textMuted }}>/ 5.0</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-xs w-20" style={{ color: COLORS.textMuted }}>Rewritten</span>
                <div className="flex-1 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.1)' }}>
                  <div 
                    className="h-full rounded-full" 
                    style={{ 
                      width: `${((rewriterData.qualityScores?.rewritten?.completeness || 0) / 5) * 100}%`,
                      background: COLORS.purple 
                    }} 
                  />
                </div>
                <span className="text-sm font-bold w-8" style={{ color: COLORS.purple }}>
                  {rewriterData.qualityScores?.rewritten?.completeness?.toFixed(1) || '0.0'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs w-20" style={{ color: COLORS.textMuted }}>Passthrough</span>
                <div className="flex-1 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.1)' }}>
                  <div 
                    className="h-full rounded-full" 
                    style={{ 
                      width: `${((rewriterData.qualityScores?.passthrough?.completeness || 0) / 5) * 100}%`,
                      background: COLORS.orange 
                    }} 
                  />
                </div>
                <span className="text-sm font-bold w-8" style={{ color: COLORS.orange }}>
                  {rewriterData.qualityScores?.passthrough?.completeness?.toFixed(1) || '0.0'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* ================================================================== */}
      {/* EXISTING CONTENT */}
      {/* ================================================================== */}

      {/* Section Divider */}
      <div className="flex items-center gap-4">
        <div className="h-px flex-1" style={{ background: 'rgba(255,255,255,0.1)' }} />
        <span className="text-sm font-medium" style={{ color: COLORS.textMuted }}>Detailed Metrics</span>
        <div className="h-px flex-1" style={{ background: 'rgba(255,255,255,0.1)' }} />
      </div>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card delay={250}>
          <div className="text-center">
            <p className="text-sm" style={{ color: COLORS.textMuted }}>Total Queries</p>
            <p className="text-3xl font-bold mt-1" style={{ color: COLORS.textPrimary }}>
              {adoptionData.totalQueries?.toLocaleString() || 0}
            </p>
            <p className="text-xs mt-1" style={{ color: COLORS.textMuted }}>Production</p>
          </div>
        </Card>
        
        <Card delay={300}>
          <div className="text-center">
            <p className="text-sm" style={{ color: COLORS.textMuted }}>Active Users</p>
            <p className="text-3xl font-bold mt-1" style={{ color: COLORS.cyan }}>
              {adoptionData.mau || 0}
            </p>
            <p className="text-xs mt-1" style={{ color: COLORS.textMuted }}>Monthly</p>
          </div>
        </Card>
        
        <Card delay={350}>
          <div className="text-center">
            <p className="text-sm" style={{ color: COLORS.textMuted }}>Feedback</p>
            <p className="text-3xl font-bold mt-1" style={{ color: COLORS.green }}>
              {feedbackData.summary?.positiveRate || 0}%
            </p>
            <p className="text-xs mt-1" style={{ color: COLORS.textMuted }}>Positive</p>
          </div>
        </Card>
        
        <Card delay={400}>
          <div className="text-center">
            <p className="text-sm" style={{ color: COLORS.textMuted }}>Rewrite Rate</p>
            <p className="text-3xl font-bold mt-1" style={{ color: COLORS.purple }}>
              {summary?.rewriteRate || 0}%
            </p>
            <p className="text-xs mt-1" style={{ color: COLORS.textMuted }}>Queries expanded</p>
          </div>
        </Card>
      </div>

      {/* Main KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {/* Query Rewriter Section */}
        <Card delay={450}>
          <div className="flex items-center gap-2 mb-4">
            <Sparkles size={20} style={{ color: COLORS.purple }} />
            <h3 className="font-semibold" style={{ color: COLORS.textPrimary }}>Query Rewriter</h3>
          </div>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: COLORS.textMuted }}>Total Processed</span>
              <span className="font-bold" style={{ color: COLORS.textPrimary }}>{summary?.totalQueries || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: COLORS.textMuted }}>Rewritten</span>
              <span className="font-bold" style={{ color: COLORS.cyan }}>{summary?.rewrittenCount || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: COLORS.textMuted }}>Pass-through</span>
              <span className="font-bold" style={{ color: COLORS.orange }}>{summary?.passthroughCount || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: COLORS.textMuted }}>Avg Latency</span>
              <Badge variant="success">
                {rewriterData.latencyStats?.avg || 0}ms
              </Badge>
            </div>
          </div>
        </Card>

        {/* Adoption Section */}
        <Card delay={500}>
          <div className="flex items-center gap-2 mb-4">
            <Users size={20} style={{ color: COLORS.cyan }} />
            <h3 className="font-semibold" style={{ color: COLORS.textPrimary }}>Adoption</h3>
          </div>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: COLORS.textMuted }}>WAU</span>
              <span className="font-bold" style={{ color: COLORS.textPrimary }}>{adoptionData.wau || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: COLORS.textMuted }}>MAU</span>
              <span className="font-bold" style={{ color: COLORS.textPrimary }}>{adoptionData.mau || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: COLORS.textMuted }}>Stickiness</span>
              <Badge variant={adoptionData.stickiness > 25 ? 'success' : 'warning'}>
                {adoptionData.stickiness || 0}%
              </Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: COLORS.textMuted }}>Queries/User</span>
              <span className="font-bold" style={{ color: COLORS.cyan }}>{adoptionData.queriesPerUser || 0}</span>
            </div>
          </div>
        </Card>

        {/* Feedback Section */}
        <Card delay={550}>
          <div className="flex items-center gap-2 mb-4">
            <ThumbsUp size={20} style={{ color: COLORS.green }} />
            <h3 className="font-semibold" style={{ color: COLORS.textPrimary }}>Feedback</h3>
          </div>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: COLORS.textMuted }}>Total</span>
              <span className="font-bold" style={{ color: COLORS.textPrimary }}>{feedbackData.summary?.total || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: COLORS.textMuted }}>Thumbs Up</span>
              <span className="font-bold" style={{ color: COLORS.green }}>{feedbackData.summary?.thumbsUp || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: COLORS.textMuted }}>Thumbs Down</span>
              <span className="font-bold" style={{ color: COLORS.red }}>{feedbackData.summary?.thumbsDown || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: COLORS.textMuted }}>Positive Rate</span>
              <Badge variant={feedbackData.summary?.positiveRate > 50 ? 'success' : 'danger'}>
                {feedbackData.summary?.positiveRate || 0}%
              </Badge>
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Links */}
      <Card delay={600}>
        <h3 className="font-semibold mb-4" style={{ color: COLORS.textPrimary }}>Quick Navigation</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <a 
            href="/query-rewriter"
            className="p-4 rounded-lg text-center transition-all hover:scale-105"
            style={{ background: 'rgba(124, 58, 237, 0.1)' }}
          >
            <Sparkles size={24} className="mx-auto mb-2" style={{ color: COLORS.purple }} />
            <p className="text-sm font-medium" style={{ color: COLORS.textPrimary }}>Query Rewriter</p>
          </a>
          
          <a 
            href="/adoption"
            className="p-4 rounded-lg text-center transition-all hover:scale-105"
            style={{ background: 'rgba(45, 212, 191, 0.1)' }}
          >
            <Users size={24} className="mx-auto mb-2" style={{ color: COLORS.cyan }} />
            <p className="text-sm font-medium" style={{ color: COLORS.textPrimary }}>Adoption</p>
          </a>
          
          <a 
            href="/feedback"
            className="p-4 rounded-lg text-center transition-all hover:scale-105"
            style={{ background: 'rgba(34, 197, 94, 0.1)' }}
          >
            <ThumbsUp size={24} className="mx-auto mb-2" style={{ color: COLORS.green }} />
            <p className="text-sm font-medium" style={{ color: COLORS.textPrimary }}>Feedback</p>
          </a>
          
          <a 
            href="/content-health"
            className="p-4 rounded-lg text-center transition-all hover:scale-105"
            style={{ background: 'rgba(239, 68, 68, 0.1)' }}
          >
            <Target size={24} className="mx-auto mb-2" style={{ color: COLORS.red }} />
            <p className="text-sm font-medium" style={{ color: COLORS.textPrimary }}>Content Health</p>
          </a>
        </div>
      </Card>
    </div>
  );
};

export default Overview;
