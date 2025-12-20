import React, { useState, useEffect, useRef } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { 
  Users, 
  UserCheck, 
  Target, 
  BarChart3, 
  Clock, 
  Calendar,
  Zap,
  X
} from 'lucide-react';
import { COLORS } from '../App';
import { Card, KPICard, Badge, PageHeader, TitleWithInfo } from '../components/ui';

// Import data
import { useApiData } from '../hooks/useApiData';

// Toast Notification Component
const QueryNotification = ({ notifications, onDismiss }) => {
  return (
    <div className="fixed right-4 top-20 z-50 space-y-2 max-h-[70vh] overflow-hidden">
      {notifications.map((notif) => (
        <div
          key={notif.id}
          className="animate-slide-in-right flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg border"
          style={{
            background: 'rgba(26, 26, 46, 0.95)',
            borderColor: 'rgba(34, 211, 238, 0.3)',
            backdropFilter: 'blur(10px)',
            minWidth: '280px',
          }}
        >
          <div 
            className="p-2 rounded-full"
            style={{ background: 'rgba(34, 211, 238, 0.2)' }}
          >
            <Zap size={16} style={{ color: COLORS.cyan }} />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium" style={{ color: COLORS.textPrimary }}>
              New Query
            </p>
            <p className="text-xs" style={{ color: COLORS.textMuted }}>
              {notif.count} new {notif.count === 1 ? 'query' : 'queries'} just came in
            </p>
          </div>
          <button 
            onClick={() => onDismiss(notif.id)}
            className="p-1 rounded hover:bg-white/10 transition-colors"
          >
            <X size={14} style={{ color: COLORS.textMuted }} />
          </button>
        </div>
      ))}
    </div>
  );
};

const Adoption = () => {
  // Fetch live data from API
  const { data, loading, error } = useApiData();
  
  // Track previous query count for notifications
  const [notifications, setNotifications] = useState([]);
  const prevQueryCount = useRef(null);
  const notifIdCounter = useRef(0);
  
  // Use adoption data from API (must be before any conditional returns for consistency)
  const adoptionData = data?.adoption || {};
  
  // Detect new queries and show notification
  useEffect(() => {
    const currentCount = adoptionData.totalQueries || 0;
    
    if (prevQueryCount.current !== null && currentCount > prevQueryCount.current) {
      const newQueries = currentCount - prevQueryCount.current;
      const newNotif = {
        id: notifIdCounter.current++,
        count: newQueries,
        timestamp: Date.now(),
      };
      
      setNotifications(prev => [newNotif, ...prev].slice(0, 5)); // Keep max 5 notifications
      
      // Auto-dismiss after 5 seconds
      setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== newNotif.id));
      }, 5000);
    }
    
    prevQueryCount.current = currentCount;
  }, [adoptionData.totalQueries]);
  
  const dismissNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p style={{ color: COLORS.textMuted }}>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Live Query Notifications */}
      <QueryNotification 
        notifications={notifications} 
        onDismiss={dismissNotification} 
      />
      
      <PageHeader 
        title="Adoption & Engagement"
        subtitle={`Production usage metrics from ${(adoptionData.totalQueries || 0).toLocaleString()} total queries`}
        icon={Users}
        badge={
          <Badge variant={adoptionData.stickiness > 25 ? 'success' : 'warning'}>
            <Target size={12} />
            {adoptionData.stickiness || 0}% stickiness
          </Badge>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Weekly Active Users"
          value={adoptionData.wau || 0}
          subtitle="Last 7 days"
          icon={UserCheck}
          delay={100}
          tooltip="Unique users who queried Nexus in the past 7 days."
        />
        <KPICard
          title="Monthly Active Users"
          value={adoptionData.mau || 0}
          subtitle="Last 30 days"
          icon={Users}
          delay={200}
          tooltip="Unique users who queried Nexus in the past 30 days."
        />
        <KPICard
          title="Stickiness"
          value={`${adoptionData.stickiness || 0}%`}
          subtitle="WAU / MAU ratio"
          icon={Target}
          trend={adoptionData.stickiness > 25 ? 'positive' : 'negative'}
          trendLabel={adoptionData.stickiness > 25 ? 'Above 25% target' : 'Below 25% target'}
          delay={300}
          tooltip="Percentage of monthly users who return weekly. Higher = more engaged users."
        />
        <KPICard
          title="Queries per User"
          value={adoptionData.queriesPerUser || 0}
          subtitle={`${(adoptionData.totalUsers || 0).toLocaleString()} total users`}
          icon={BarChart3}
          delay={400}
          tooltip="Average number of queries per unique user."
        />
      </div>

      {/* Query Trend Chart */}
      <Card delay={500}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <TitleWithInfo tooltip="Daily query volume over the past 30 days.">
              Daily Query Volume
            </TitleWithInfo>
            <p className="text-sm mt-1" style={{ color: COLORS.textMuted }}>
              Last 30 days of production usage
            </p>
          </div>
          <Badge>
            <Calendar size={12} />
            Peak hour: {adoptionData.peakHour || 0}:00
          </Badge>
        </div>
        
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={adoptionData.queryTrend || []} 
              margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis 
                dataKey="date" 
                tick={{ fill: COLORS.textMuted, fontSize: 10 }}
                tickFormatter={(value) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              <YAxis 
                tick={{ fill: COLORS.textMuted, fontSize: 12 }}
              />
              <Tooltip 
                contentStyle={{ 
                  background: COLORS.surface, 
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: COLORS.textPrimary }}
                itemStyle={{ color: COLORS.cyan }}
              />
              <Bar 
                dataKey="count" 
                fill={COLORS.cyan}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Response Time Card */}
        <Card delay={600}>
          <div className="flex items-center justify-between mb-6">
            <div>
              <TitleWithInfo tooltip="Average time for LLM to generate responses.">
                Average Response Time
              </TitleWithInfo>
              <p className="text-sm mt-1" style={{ color: COLORS.textMuted }}>
                LLM generation latency
              </p>
            </div>
            <div className="p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.05)' }}>
              <Clock size={24} style={{ color: COLORS.orange }} />
            </div>
          </div>
          
          <div className="text-center py-8">
            <p className="text-5xl font-extrabold tracking-tight" style={{ color: COLORS.textPrimary }}>
              {((adoptionData.avgResponseTimeMs || 0) / 1000).toFixed(1)}
              <span className="text-2xl font-normal" style={{ color: COLORS.textMuted }}>s</span>
            </p>
            <p className="text-sm mt-2" style={{ color: COLORS.textMuted }}>
              {(adoptionData.avgResponseTimeMs || 0).toLocaleString()}ms average
            </p>
          </div>
          
          <div className="mt-4 p-4 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
            <div className="flex items-center justify-between">
              <span className="text-sm" style={{ color: COLORS.textMuted }}>Performance</span>
              <Badge variant={(adoptionData.avgResponseTimeMs || 0) < 10000 ? 'success' : 'warning'}>
                {(adoptionData.avgResponseTimeMs || 0) < 10000 ? 'Good' : 'Needs Improvement'}
              </Badge>
            </div>
          </div>
        </Card>

        {/* Top Users Card */}
        <Card delay={700}>
          <div className="flex items-center justify-between mb-6">
            <div>
              <TitleWithInfo tooltip="Most active users by query count.">
                Top Users
              </TitleWithInfo>
              <p className="text-sm mt-1" style={{ color: COLORS.textMuted }}>
                Most active users by query count
              </p>
            </div>
            <Badge>
              <Users size={12} />
              {(adoptionData.totalUsers || 0).toLocaleString()} total
            </Badge>
          </div>
          
          <div className="space-y-3">
            {(adoptionData.topUsers || []).slice(0, 7).map((user, index) => (
              <div 
                key={index}
                className="flex items-center justify-between p-3 rounded-lg"
                style={{ background: 'rgba(255,255,255,0.03)' }}
              >
                <div className="flex items-center gap-3">
                  <div 
                    className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                    style={{ 
                      background: index === 0 ? COLORS.orange : index === 1 ? COLORS.cyan : 'rgba(255,255,255,0.1)',
                      color: COLORS.textPrimary,
                    }}
                  >
                    {index + 1}
                  </div>
                  <span className="font-mono text-sm" style={{ color: COLORS.textPrimary }}>
                    {user.user}
                  </span>
                </div>
                <span className="font-semibold" style={{ color: COLORS.cyan }}>
                  {(user.queries || 0).toLocaleString()} queries
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Summary Stats */}
      <Card delay={800}>
        <TitleWithInfo tooltip="Overall usage statistics.">
          Usage Summary
        </TitleWithInfo>
        <p className="text-sm mt-1 mb-6" style={{ color: COLORS.textMuted }}>
          Key engagement metrics
        </p>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="text-center p-4 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
            <p className="text-sm" style={{ color: COLORS.textMuted }}>Total Queries</p>
            <p className="text-2xl font-bold mt-2" style={{ color: COLORS.textPrimary }}>
              {(adoptionData.totalQueries || 0).toLocaleString()}
            </p>
          </div>
          <div className="text-center p-4 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
            <p className="text-sm" style={{ color: COLORS.textMuted }}>Total Users</p>
            <p className="text-2xl font-bold mt-2" style={{ color: COLORS.cyan }}>
              {(adoptionData.totalUsers || 0).toLocaleString()}
            </p>
          </div>
          <div className="text-center p-4 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
            <p className="text-sm" style={{ color: COLORS.textMuted }}>Peak Hour</p>
            <p className="text-2xl font-bold mt-2" style={{ color: COLORS.orange }}>
              {adoptionData.peakHour || 0}:00
            </p>
          </div>
          <div className="text-center p-4 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
            <p className="text-sm" style={{ color: COLORS.textMuted }}>Avg Response</p>
            <p className="text-2xl font-bold mt-2" style={{ color: COLORS.purple }}>
              {((adoptionData.avgResponseTimeMs || 0) / 1000).toFixed(1)}s
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Adoption;
