import React, { useState, useMemo } from 'react';
import { 
  Database, 
  AlertTriangle, 
  Search,
  ChevronDown,
  ChevronUp,
  XCircle,
  Target
} from 'lucide-react';
import { COLORS } from '../App';
import { Card, KPICard, Badge, PageHeader, TitleWithInfo } from '../components/ui';

// Import data
import { useApiData } from '../hooks/useApiData';

const ContentHealth = () => {
  // Fetch live data from API
  const { data: apiData, loading, error } = useApiData();

  const [searchTerm, setSearchTerm] = useState('');
  const [filterRewritten, setFilterRewritten] = useState('all');
  const [expandedRows, setExpandedRows] = useState(new Set());

  // Use rewriter data from API (must be before any conditional returns to follow Rules of Hooks)
  const rewriterData = apiData?.rewriter || {};
  const zeroResultQueries = rewriterData.zeroResultQueries || [];

  // Filter queries - useMemo must be called on every render (before any early returns)
  const filteredQueries = useMemo(() => {
    return zeroResultQueries.filter(item => {
      // Filter by rewritten status
      if (filterRewritten === 'yes' && !item.wasRewritten) return false;
      if (filterRewritten === 'no' && item.wasRewritten) return false;
      
      // Filter by search term
      if (searchTerm && !item.query?.toLowerCase().includes(searchTerm.toLowerCase())) return false;
      
      return true;
    });
  }, [filterRewritten, searchTerm, zeroResultQueries]);

  // Stats
  const rewrittenZeros = zeroResultQueries.filter(q => q.wasRewritten).length;
  const passthroughZeros = zeroResultQueries.filter(q => !q.wasRewritten).length;

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

  // Loading state - AFTER all hooks are called
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p style={{ color: COLORS.textMuted }}>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader 
        title="Content Health"
        subtitle="Zero-result queries and content gaps"
        icon={Database}
        badge={
          <Badge variant="warning">
            <AlertTriangle size={12} />
            {zeroResultQueries.length} gaps identified
          </Badge>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Zero-Result Queries"
          value={zeroResultQueries.length}
          subtitle="Total content gaps"
          icon={XCircle}
          delay={100}
          tooltip="Queries that returned no search results."
        />
        <KPICard
          title="Rewritten Zeros"
          value={rewrittenZeros}
          subtitle="With entity expansion"
          icon={AlertTriangle}
          delay={200}
          tooltip="Zero-result queries that were expanded but still returned no results."
        />
        <KPICard
          title="Pass-through Zeros"
          value={passthroughZeros}
          subtitle="No entities matched"
          icon={Target}
          delay={300}
          tooltip="Zero-result queries where no entities were detected."
        />
        <KPICard
          title="Zero Rate"
          value={`${rewriterData.effectiveness?.rewrittenZeroRate || 0}%`}
          subtitle="Rewritten queries"
          icon={Database}
          trend={(rewriterData.effectiveness?.rewrittenZeroRate || 0) < 20 ? 'positive' : 'negative'}
          trendLabel={(rewriterData.effectiveness?.rewrittenZeroRate || 0) < 20 ? 'Good' : 'Needs work'}
          delay={400}
          tooltip="Percentage of rewritten queries that returned zero results."
        />
      </div>

      {/* Content Gap Analysis */}
      <Card delay={500}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
          <div>
            <TitleWithInfo tooltip="Queries that returned no search results, indicating missing content.">
              Zero-Result Queries
            </TitleWithInfo>
            <p className="text-sm mt-1" style={{ color: COLORS.textMuted }}>
              {filteredQueries.length} of {zeroResultQueries.length} queries shown
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
                placeholder="Search queries..."
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
            
            {/* Rewritten Filter */}
            <select
              value={filterRewritten}
              onChange={(e) => setFilterRewritten(e.target.value)}
              className="px-4 py-2 rounded-lg text-sm"
              style={{ 
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                color: COLORS.textPrimary,
              }}
            >
              <option value="all">All Queries</option>
              <option value="yes">Rewritten Only</option>
              <option value="no">Pass-through Only</option>
            </select>
          </div>
        </div>
        
        {/* Queries List */}
        <div className="space-y-2">
          {filteredQueries.slice(0, 30).map((item, index) => (
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
                {/* Status Icon */}
                <div 
                  className="p-2 rounded-lg"
                  style={{ background: 'rgba(239, 68, 68, 0.15)' }}
                >
                  <XCircle size={16} style={{ color: COLORS.red }} />
                </div>
                
                {/* Query */}
                <div className="flex-1 min-w-0">
                  <p 
                    className="text-sm truncate font-medium" 
                    style={{ color: COLORS.textPrimary }}
                  >
                    {item.query || 'No query'}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs" style={{ color: COLORS.textMuted }}>
                      {item.wasRewritten ? 'Rewritten' : 'Pass-through'}
                    </span>
                    {item.matchedEntities?.length > 0 && (
                      <>
                        <span className="text-xs" style={{ color: COLORS.textMuted }}>•</span>
                        <span className="text-xs" style={{ color: COLORS.purple }}>
                          {item.matchedEntities.length} entities matched
                        </span>
                      </>
                    )}
                  </div>
                </div>
                
                {/* Status Badge */}
                <Badge variant={item.wasRewritten ? 'info' : 'warning'}>
                  {item.wasRewritten ? 'Expanded' : 'No Match'}
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
                  <div className="pt-4 space-y-4">
                    <div>
                      <p className="text-xs font-medium mb-1" style={{ color: COLORS.textMuted }}>
                        Full Query
                      </p>
                      <p className="text-sm" style={{ color: COLORS.textPrimary }}>
                        {item.query}
                      </p>
                    </div>
                    
                    {item.matchedEntities?.length > 0 && (
                      <div>
                        <p className="text-xs font-medium mb-2" style={{ color: COLORS.textMuted }}>
                          Matched Entities
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {item.matchedEntities.map((entity, i) => (
                            <span 
                              key={i}
                              className="px-2 py-1 rounded text-xs font-medium"
                              style={{ 
                                background: 'rgba(124, 58, 237, 0.2)',
                                color: COLORS.purple,
                              }}
                            >
                              {entity}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div className="p-3 rounded-lg" style={{ background: 'rgba(234, 179, 8, 0.1)' }}>
                      <div className="flex items-start gap-2">
                        <Target size={16} style={{ color: '#eab308' }} className="mt-0.5" />
                        <div>
                          <p className="text-xs font-medium" style={{ color: '#eab308' }}>
                            Recommended Action
                          </p>
                          <p className="text-sm mt-1" style={{ color: COLORS.textPrimary }}>
                            {item.wasRewritten 
                              ? 'Content exists in ontology but not in index. Check if related documents need to be added to the knowledge base.'
                              : 'No entities matched. Consider adding relevant terms to the ontology lexicon.'
                            }
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        
        {filteredQueries.length > 30 && (
          <p className="text-center text-sm mt-4" style={{ color: COLORS.textMuted }}>
            Showing 30 of {filteredQueries.length} items. Use filters to narrow results.
          </p>
        )}
        
        {filteredQueries.length === 0 && (
          <div className="text-center py-12">
            <Database size={48} className="mx-auto mb-4" style={{ color: COLORS.textMuted }} />
            <p style={{ color: COLORS.textMuted }}>No zero-result queries match your filters.</p>
          </div>
        )}
      </Card>

      {/* Recommendations */}
      <Card delay={600}>
        <TitleWithInfo tooltip="Suggested actions to improve content coverage.">
          Content Improvement Recommendations
        </TitleWithInfo>
        <p className="text-sm mt-1 mb-6" style={{ color: COLORS.textMuted }}>
          Based on zero-result query analysis
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div 
            className="p-4 rounded-lg border border-white/5"
            style={{ background: 'rgba(124, 58, 237, 0.1)' }}
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1.5 rounded" style={{ background: 'rgba(124, 58, 237, 0.2)' }}>
                <Target size={14} style={{ color: COLORS.purple }} />
              </div>
              <h4 className="font-medium" style={{ color: COLORS.textPrimary }}>
                Expand Ontology
              </h4>
            </div>
            <p className="text-sm" style={{ color: COLORS.textMuted }}>
              Add missing terms to lexicon based on pass-through queries that returned zero results.
            </p>
          </div>
          
          <div 
            className="p-4 rounded-lg border border-white/5"
            style={{ background: 'rgba(45, 212, 191, 0.1)' }}
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1.5 rounded" style={{ background: 'rgba(45, 212, 191, 0.2)' }}>
                <Database size={14} style={{ color: COLORS.cyan }} />
              </div>
              <h4 className="font-medium" style={{ color: COLORS.textPrimary }}>
                Update Indexes
              </h4>
            </div>
            <p className="text-sm" style={{ color: COLORS.textMuted }}>
              Add new documents or update existing content for queries where entities matched but no results were found.
            </p>
          </div>
          
          <div 
            className="p-4 rounded-lg border border-white/5"
            style={{ background: 'rgba(234, 179, 8, 0.1)' }}
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1.5 rounded" style={{ background: 'rgba(234, 179, 8, 0.2)' }}>
                <AlertTriangle size={14} style={{ color: '#eab308' }} />
              </div>
              <h4 className="font-medium" style={{ color: COLORS.textPrimary }}>
                Review Synonyms
              </h4>
            </div>
            <p className="text-sm" style={{ color: COLORS.textMuted }}>
              Check if existing entities need additional synonyms or variations to catch more queries.
            </p>
          </div>
          
          <div 
            className="p-4 rounded-lg border border-white/5"
            style={{ background: 'rgba(239, 68, 68, 0.1)' }}
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1.5 rounded" style={{ background: 'rgba(239, 68, 68, 0.2)' }}>
                <XCircle size={14} style={{ color: COLORS.red }} />
              </div>
              <h4 className="font-medium" style={{ color: COLORS.textPrimary }}>
                Out-of-Scope Detection
              </h4>
            </div>
            <p className="text-sm" style={{ color: COLORS.textMuted }}>
              Identify queries that are outside Nexus's domain and improve user guidance messaging.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ContentHealth;
