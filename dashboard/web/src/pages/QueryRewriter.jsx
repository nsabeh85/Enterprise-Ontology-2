import React from 'react';
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
  Sparkles, 
  Zap, 
  CheckCircle2, 
  TrendingUp,
  Clock
} from 'lucide-react';
import { COLORS } from '../App';
import { Card, KPICard, Badge, PageHeader, TitleWithInfo, CustomChartTooltip, ScoreBar } from '../components/ui';

// Import data
import { useApiData } from '../hooks/useApiData';

const QueryRewriter = () => {
  // Fetch live data from API
  const { data, loading, error } = useApiData();

  // Use rewriter data from API (must be before any conditional returns)
  const rewriterData = data?.rewriter || {};
  const { summary, effectiveness, latencyStats, qualityScores, topEntities, rewrittenQueries } = rewriterData;
  const ENTITY_COLORS = [COLORS.purple, COLORS.cyan, COLORS.orange, COLORS.pink, COLORS.red];

  // Transform entity data for pie chart
  const entityChartData = (topEntities || []).map((item, index) => ({
    name: item.entity,
    value: item.count,
    fill: ENTITY_COLORS[index % ENTITY_COLORS.length],
  }));

  // Data for effectiveness comparison
  const effectivenessData = [
    { 
      name: 'Rewritten', 
      zeroRate: effectiveness?.rewrittenZeroRate || 0, 
      avgResults: effectiveness?.rewrittenAvgResults || 0,
      fill: COLORS.cyan 
    },
    { 
      name: 'Pass-through', 
      zeroRate: effectiveness?.passthroughZeroRate || 0, 
      avgResults: effectiveness?.passthroughAvgResults || 0,
      fill: COLORS.orange 
    },
  ];

  // Loading state - AFTER all hooks and data processing
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p style={{ color: COLORS.textMuted }}>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader 
        title="Query Rewriter Performance"
        subtitle="Ontology-aware query expansion metrics"
        icon={Sparkles}
        badge={
          <Badge variant="success">
            <CheckCircle2 size={12} />
            {summary?.rewriteRate || 0}% rewrite rate
          </Badge>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Queries"
          value={summary?.totalQueries || 0}
          subtitle="Processed through rewriter"
          icon={Sparkles}
          delay={100}
          tooltip="Total queries that passed through the query rewriter system."
        />
        <KPICard
          title="Rewritten"
          value={summary?.rewrittenCount || 0}
          subtitle={`${summary?.rewriteRate || 0}% of queries`}
          icon={TrendingUp}
          trend="positive"
          trendLabel="Entities matched"
          delay={200}
          tooltip="Queries where entities were detected and synonyms were expanded."
        />
        <KPICard
          title="Pass-through"
          value={summary?.passthroughCount || 0}
          subtitle="No entities matched"
          icon={Zap}
          delay={300}
          tooltip="Queries that passed through unchanged (no entity matches found)."
        />
        <KPICard
          title="Avg Latency"
          value={`${latencyStats?.avg || 0}ms`}
          icon={Clock}
          trend="positive"
          trendLabel={`Under ${latencyStats?.target || 40}ms target`}
          delay={400}
          tooltip="Average time to process and expand a query."
        />
      </div>

      {/* Effectiveness Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Zero-Result Comparison */}
        <Card delay={500}>
          <TitleWithInfo tooltip="Percentage of queries that returned zero search results. Lower is better.">
            Zero-Result Rate Comparison
          </TitleWithInfo>
          <p className="text-sm mt-1 mb-6" style={{ color: COLORS.textMuted }}>
            Rewritten vs pass-through queries
          </p>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={effectivenessData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis 
                  type="number" 
                  domain={[0, 30]} 
                  tick={{ fill: COLORS.textMuted, fontSize: 12 }}
                  tickFormatter={(v) => `${v}%`}
                />
                <YAxis 
                  type="category" 
                  dataKey="name" 
                  tick={{ fill: COLORS.textMuted, fontSize: 12 }}
                  width={100}
                />
                <Tooltip content={<CustomChartTooltip />} />
                <Bar 
                  dataKey="zeroRate" 
                  radius={[0, 6, 6, 0]}
                  label={{ 
                    position: 'right', 
                    fill: COLORS.textPrimary,
                    fontSize: 14,
                    fontWeight: 600,
                    formatter: (v) => `${v}%`
                  }}
                >
                  {effectivenessData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Average Results Comparison */}
        <Card delay={600}>
          <TitleWithInfo tooltip="Mean number of documents returned by search. Higher indicates better recall.">
            Average Results per Query
          </TitleWithInfo>
          <p className="text-sm mt-1 mb-6" style={{ color: COLORS.textMuted }}>
            Search result counts by group
          </p>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={effectivenessData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis 
                  type="number" 
                  domain={[0, 50]} 
                  tick={{ fill: COLORS.textMuted, fontSize: 12 }}
                />
                <YAxis 
                  type="category" 
                  dataKey="name" 
                  tick={{ fill: COLORS.textMuted, fontSize: 12 }}
                  width={100}
                />
                <Tooltip content={<CustomChartTooltip />} />
                <Bar 
                  dataKey="avgResults" 
                  radius={[0, 6, 6, 0]}
                  label={{ 
                    position: 'right', 
                    fill: COLORS.textPrimary,
                    fontSize: 14,
                    fontWeight: 600,
                  }}
                >
                  {effectivenessData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Latency Stats */}
      <Card delay={700}>
        <TitleWithInfo tooltip="Time to process and expand queries through the optimizer.">
          Query Rewrite Latency
        </TitleWithInfo>
        <p className="text-sm mt-1 mb-6" style={{ color: COLORS.textMuted }}>
          Performance statistics (target: {latencyStats?.target || 40}ms)
        </p>
        
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
          <div className="text-center p-4 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
            <p className="text-sm" style={{ color: COLORS.textMuted }}>Minimum</p>
            <p className="text-3xl font-bold mt-2" style={{ color: COLORS.cyan }}>
              {latencyStats?.min || 0}<span className="text-lg font-normal">ms</span>
            </p>
          </div>
          <div className="text-center p-4 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
            <p className="text-sm" style={{ color: COLORS.textMuted }}>Maximum</p>
            <p className="text-3xl font-bold mt-2" style={{ color: COLORS.orange }}>
              {latencyStats?.max || 0}<span className="text-lg font-normal">ms</span>
            </p>
          </div>
          <div className="text-center p-4 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
            <p className="text-sm" style={{ color: COLORS.textMuted }}>Average</p>
            <p className="text-3xl font-bold mt-2" style={{ color: COLORS.purple }}>
              {latencyStats?.avg || 0}<span className="text-lg font-normal">ms</span>
            </p>
          </div>
          <div className="text-center p-4 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
            <p className="text-sm" style={{ color: COLORS.textMuted }}>p95</p>
            <p className="text-3xl font-bold mt-2" style={{ color: COLORS.pink }}>
              {latencyStats?.p95 || 0}<span className="text-lg font-normal">ms</span>
            </p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-6 pt-6 border-t border-white/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm" style={{ color: COLORS.textMuted }}>Max vs Target</span>
            <span className="text-sm font-medium" style={{ color: COLORS.textPrimary }}>
              {latencyStats?.max || 0}ms / {latencyStats?.target || 40}ms
            </span>
          </div>
          <div className="h-3 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.1)' }}>
            <div 
              className="h-full rounded-full"
              style={{ 
                width: `${Math.min(((latencyStats?.max || 0) / (latencyStats?.target || 40)) * 100, 100)}%`,
                background: `linear-gradient(90deg, ${COLORS.cyan}, ${COLORS.purple})`,
              }}
            />
          </div>
        </div>
      </Card>

      {/* Quality Scores */}
      {qualityScores && (
        <Card delay={800}>
          <TitleWithInfo tooltip="LLM-as-judge evaluation scores (1-5 scale).">
            Answer Quality Scores
          </TitleWithInfo>
          <p className="text-sm mt-1 mb-6" style={{ color: COLORS.textMuted }}>
            Comparing rewritten vs pass-through queries
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {['relevance', 'groundedness', 'completeness'].map((metric) => (
              <div key={metric} className="p-4 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
                <h4 className="text-sm font-medium capitalize mb-4" style={{ color: COLORS.textMuted }}>
                  {metric}
                </h4>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-xs" style={{ color: COLORS.cyan }}>Rewritten</span>
                      <span className="text-sm font-bold" style={{ color: COLORS.cyan }}>
                        {qualityScores.rewritten?.[metric] || 0}
                      </span>
                    </div>
                    <ScoreBar score={qualityScores.rewritten?.[metric] || 0} color={COLORS.cyan} />
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-xs" style={{ color: COLORS.orange }}>Pass-through</span>
                      <span className="text-sm font-bold" style={{ color: COLORS.orange }}>
                        {qualityScores.passthrough?.[metric] || 0}
                      </span>
                    </div>
                    <ScoreBar score={qualityScores.passthrough?.[metric] || 0} color={COLORS.orange} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Entity Match Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card delay={900}>
          <TitleWithInfo tooltip="Most frequently matched entities across queries.">
            Top Matched Entities
          </TitleWithInfo>
          <p className="text-sm mt-1 mb-6" style={{ color: COLORS.textMuted }}>
            Entity detection frequency
          </p>
          
          <div className="space-y-3">
            {(topEntities || []).slice(0, 8).map((entity, index) => (
              <div key={index} className="flex items-center gap-3">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ background: ENTITY_COLORS[index % ENTITY_COLORS.length] }}
                />
                <span className="flex-1 text-sm" style={{ color: COLORS.textMuted }}>
                  {entity.entity}
                </span>
                <span className="font-bold" style={{ color: COLORS.textPrimary }}>
                  {entity.count}
                </span>
              </div>
            ))}
          </div>
        </Card>

        <Card delay={950}>
          <TitleWithInfo tooltip="Visual distribution of entity matches.">
            Entity Distribution
          </TitleWithInfo>
          <p className="text-sm mt-1 mb-6" style={{ color: COLORS.textMuted }}>
            Proportional breakdown
          </p>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={entityChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                  stroke="none"
                >
                  {entityChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip content={<CustomChartTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Rewritten Queries Table */}
      <Card delay={1000}>
        <TitleWithInfo tooltip="Queries that were expanded with entity matches.">
          Rewritten Queries
        </TitleWithInfo>
        <p className="text-sm mt-1 mb-6" style={{ color: COLORS.textMuted }}>
          {(rewrittenQueries || []).length} queries with entity expansion
        </p>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-3 px-4 text-sm font-semibold" style={{ color: COLORS.textMuted }}>Query</th>
                <th className="text-left py-3 px-4 text-sm font-semibold" style={{ color: COLORS.textMuted }}>Entities</th>
                <th className="text-center py-3 px-4 text-sm font-semibold" style={{ color: COLORS.textMuted }}>Expansions</th>
                <th className="text-center py-3 px-4 text-sm font-semibold" style={{ color: COLORS.textMuted }}>Time</th>
                <th className="text-center py-3 px-4 text-sm font-semibold" style={{ color: COLORS.textMuted }}>Results</th>
              </tr>
            </thead>
            <tbody>
              {(rewrittenQueries || []).slice(0, 20).map((row, index) => (
                <tr 
                  key={row.id || index} 
                  className="border-b border-white/5 transition-colors hover:bg-white/5"
                >
                  <td className="py-4 px-4 max-w-xs">
                    <span className="font-medium truncate block" style={{ color: COLORS.textPrimary }}>
                      {row.query}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex flex-wrap gap-1">
                      {(row.matchedEntities || []).map((entity, i) => (
                        <span 
                          key={i}
                          className="px-2 py-0.5 rounded text-xs font-medium"
                          style={{ 
                            background: 'rgba(124, 58, 237, 0.2)',
                            color: COLORS.purple,
                          }}
                        >
                          {entity}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span className="font-mono text-sm" style={{ color: COLORS.textPrimary }}>
                      {row.expansionCount}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span 
                      className="font-mono text-sm px-2 py-1 rounded"
                      style={{ 
                        background: row.rewriteTimeMs < 5 ? 'rgba(34, 197, 94, 0.15)' : 'rgba(234, 179, 8, 0.15)',
                        color: row.rewriteTimeMs < 5 ? '#22c55e' : '#eab308',
                      }}
                    >
                      {row.rewriteTimeMs}ms
                    </span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span 
                      className="inline-flex items-center justify-center w-10 h-10 rounded-full font-bold"
                      style={{ 
                        background: `linear-gradient(135deg, ${COLORS.cyan}33, ${COLORS.purple}33)`,
                        color: COLORS.textPrimary,
                      }}
                    >
                      {row.resultCount}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default QueryRewriter;
