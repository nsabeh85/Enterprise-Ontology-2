import React, { useState, useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { 
  MessageSquare, 
  ThumbsUp, 
  ThumbsDown, 
  Search,
  Filter,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { COLORS } from '../App';
import { Card, KPICard, Badge, PageHeader, TitleWithInfo, CustomChartTooltip } from '../components/ui';

// Import data
import { useApiData } from '../hooks/useApiData';

const Feedback = () => {
  // Fetch live data from API
  const { data, loading, error } = useApiData();

  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterCategory, setFilterCategory] = useState('all');
  const [expandedRows, setExpandedRows] = useState(new Set());

  // Use feedback data from API (must be before any conditional returns)
  const feedbackData = data?.feedback || {};

  const CATEGORY_COLORS = {
    'ServiceFabric': COLORS.purple,
    'Capacity': COLORS.cyan,
    'Connectivity': COLORS.orange,
    'Facilities': COLORS.pink,
    'General Info': COLORS.green,
    'Out-of-Scope': COLORS.red,
    'Other': '#6b7280',
    'Uncategorized': '#6b7280',
  };

  // Get unique categories - useMemo must be called before any early returns
  const categories = useMemo(() => {
    const cats = new Set((feedbackData.feedbackItems || []).map(f => f.category));
    return ['all', ...Array.from(cats)];
  }, [feedbackData.feedbackItems]);

  // Filter feedback items
  const filteredFeedback = useMemo(() => {
    return (feedbackData.feedbackItems || []).filter(item => {
      // Filter by type
      if (filterType !== 'all' && item.feedbackType !== filterType) return false;
      
      // Filter by category
      if (filterCategory !== 'all' && item.category !== filterCategory) return false;
      
      // Filter by search term
      if (searchTerm && !item.comment?.toLowerCase().includes(searchTerm.toLowerCase())) return false;
      
      return true;
    });
  }, [filterType, filterCategory, searchTerm, feedbackData.feedbackItems]);

  // Loading state - AFTER all hooks
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p style={{ color: COLORS.textMuted }}>Loading...</p>
        </div>
      </div>
    );
  }

  // Category chart data
  const categoryChartData = (feedbackData.categoryBreakdown || []).map(item => ({
    name: item.category,
    value: item.count,
    fill: CATEGORY_COLORS[item.category] || '#6b7280',
  }));

  // Trend data
  const trendData = feedbackData.trend || [];

  // Toggle row expansion
  const toggleRow = (id) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  return (
    <div className="space-y-8">
      <PageHeader 
        title="User Feedback Analysis"
        subtitle={`${feedbackData.summary?.total || 0} feedback items analyzed`}
        icon={MessageSquare}
        badge={
          <Badge variant={feedbackData.summary?.positiveRate > 50 ? 'success' : 'danger'}>
            <ThumbsUp size={12} />
            {feedbackData.summary?.positiveRate || 0}% positive
          </Badge>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Feedback"
          value={feedbackData.summary?.total || 0}
          subtitle="All time"
          icon={MessageSquare}
          delay={100}
          tooltip="Total number of feedback items received."
        />
        <KPICard
          title="Thumbs Up"
          value={feedbackData.summary?.thumbsUp || 0}
          subtitle={`${feedbackData.summary?.positiveRate || 0}% of total`}
          icon={ThumbsUp}
          trend="positive"
          trendLabel="Positive feedback"
          delay={200}
          tooltip="Number of positive (thumbs up) feedback."
        />
        <KPICard
          title="Thumbs Down"
          value={feedbackData.summary?.thumbsDown || 0}
          subtitle={`${(100 - (feedbackData.summary?.positiveRate || 0)).toFixed(1)}% of total`}
          icon={ThumbsDown}
          delay={300}
          tooltip="Number of negative (thumbs down) feedback."
        />
        <KPICard
          title="Categories"
          value={(feedbackData.categoryBreakdown || []).length}
          subtitle="AI-identified themes"
          icon={Filter}
          delay={400}
          tooltip="Number of distinct feedback categories identified by AI."
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Category Breakdown */}
        <Card delay={500}>
          <TitleWithInfo tooltip="AI-categorized feedback themes.">
            Feedback by Category
          </TitleWithInfo>
          <p className="text-sm mt-1 mb-6" style={{ color: COLORS.textMuted }}>
            AI-identified topic distribution
          </p>
          
          <div className="flex gap-6">
            <div className="flex-1 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                    stroke="none"
                  >
                    {categoryChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomChartTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            <div className="w-40 space-y-2">
              {categoryChartData.slice(0, 6).map((item, index) => (
                <div key={index} className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ background: item.fill }}
                  />
                  <span className="text-xs truncate" style={{ color: COLORS.textMuted }}>
                    {item.name}
                  </span>
                  <span className="text-xs font-bold ml-auto" style={{ color: COLORS.textPrimary }}>
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Feedback Trend */}
        <Card delay={600}>
          <TitleWithInfo tooltip="Feedback volume over time.">
            Feedback Trend
          </TitleWithInfo>
          <p className="text-sm mt-1 mb-6" style={{ color: COLORS.textMuted }}>
            Positive vs negative over last 30 days
          </p>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trendData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fill: COLORS.textMuted, fontSize: 10 }}
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis tick={{ fill: COLORS.textMuted, fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ 
                    background: COLORS.surface, 
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="positive" name="Positive" fill={COLORS.green} stackId="a" />
                <Bar dataKey="negative" name="Negative" fill={COLORS.red} stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Feedback Table with Filters */}
      <Card delay={700}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
          <div>
            <TitleWithInfo tooltip="Filterable list of all feedback items.">
              Feedback Details
            </TitleWithInfo>
            <p className="text-sm mt-1" style={{ color: COLORS.textMuted }}>
              {filteredFeedback.length} of {feedbackData.feedbackItems?.length || 0} items shown
            </p>
          </div>
          
          {/* Filters */}
          <div className="flex flex-wrap gap-3">
            {/* Search */}
            <div className="relative">
              <Search 
                size={16} 
                className="absolute left-3 top-1/2 -translate-y-1/2"
                style={{ color: COLORS.textMuted }}
              />
              <input
                type="text"
                placeholder="Search feedback..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 pr-4 py-2 rounded-lg text-sm w-48"
                style={{ 
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  color: COLORS.textPrimary,
                }}
              />
            </div>
            
            {/* Type Filter */}
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-4 py-2 rounded-lg text-sm"
              style={{ 
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                color: COLORS.textPrimary,
              }}
            >
              <option value="all">All Types</option>
              <option value="thumbsUp">Thumbs Up</option>
              <option value="thumbsDown">Thumbs Down</option>
            </select>
            
            {/* Category Filter */}
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="px-4 py-2 rounded-lg text-sm"
              style={{ 
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                color: COLORS.textPrimary,
              }}
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>
                  {cat === 'all' ? 'All Categories' : cat}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        {/* Table */}
        <div className="space-y-2">
          {filteredFeedback.slice(0, 50).map((item, index) => (
            <div 
              key={item.id || index}
              className="rounded-lg border border-white/5 overflow-hidden transition-all"
              style={{ background: 'rgba(255,255,255,0.02)' }}
            >
              {/* Row Header */}
              <div 
                className="flex items-center gap-4 p-4 cursor-pointer hover:bg-white/5"
                onClick={() => toggleRow(item.id || index)}
              >
                {/* Type Icon */}
                <div 
                  className="p-2 rounded-lg"
                  style={{ 
                    background: item.feedbackType === 'thumbsUp' 
                      ? 'rgba(34, 197, 94, 0.15)' 
                      : 'rgba(239, 68, 68, 0.15)'
                  }}
                >
                  {item.feedbackType === 'thumbsUp' 
                    ? <ThumbsUp size={16} style={{ color: COLORS.green }} />
                    : <ThumbsDown size={16} style={{ color: COLORS.red }} />
                  }
                </div>
                
                {/* Content Preview */}
                <div className="flex-1 min-w-0">
                  <p 
                    className="text-sm truncate" 
                    style={{ color: COLORS.textPrimary }}
                  >
                    {item.comment || 'No comment'}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs" style={{ color: COLORS.textMuted }}>
                      {item.userName || 'Anonymous'}
                    </span>
                    <span className="text-xs" style={{ color: COLORS.textMuted }}>•</span>
                    <span className="text-xs" style={{ color: COLORS.textMuted }}>
                      {new Date(item.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                
                {/* Category Badge */}
                <Badge 
                  variant={item.feedbackType === 'thumbsUp' ? 'success' : 'danger'}
                >
                  {item.category || 'Uncategorized'}
                </Badge>
                
                {/* Expand Icon */}
                {expandedRows.has(item.id || index) 
                  ? <ChevronUp size={16} style={{ color: COLORS.textMuted }} />
                  : <ChevronDown size={16} style={{ color: COLORS.textMuted }} />
                }
              </div>
              
              {/* Expanded Content */}
              {expandedRows.has(item.id || index) && (
                <div 
                  className="px-4 pb-4 border-t border-white/5"
                  style={{ background: 'rgba(0,0,0,0.2)' }}
                >
                  <div className="pt-4 space-y-3">
                    <div>
                      <p className="text-xs font-medium mb-1" style={{ color: COLORS.textMuted }}>
                        Full Comment
                      </p>
                      <p className="text-sm" style={{ color: COLORS.textPrimary }}>
                        {item.comment || 'No comment provided'}
                      </p>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
                      <div>
                        <p className="text-xs" style={{ color: COLORS.textMuted }}>User</p>
                        <p className="text-sm font-medium" style={{ color: COLORS.textPrimary }}>
                          {item.userName || 'Anonymous'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs" style={{ color: COLORS.textMuted }}>Timestamp</p>
                        <p className="text-sm font-medium" style={{ color: COLORS.textPrimary }}>
                          {new Date(item.timestamp).toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs" style={{ color: COLORS.textMuted }}>Category</p>
                        <p className="text-sm font-medium" style={{ color: CATEGORY_COLORS[item.category] || COLORS.textPrimary }}>
                          {item.category || 'Uncategorized'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs" style={{ color: COLORS.textMuted }}>Conversation ID</p>
                        <p className="text-sm font-mono" style={{ color: COLORS.textMuted }}>
                          {item.conversationId || 'N/A'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        
        {filteredFeedback.length > 50 && (
          <p className="text-center text-sm mt-4" style={{ color: COLORS.textMuted }}>
            Showing 50 of {filteredFeedback.length} items. Use filters to narrow results.
          </p>
        )}
      </Card>
    </div>
  );
};

export default Feedback;
