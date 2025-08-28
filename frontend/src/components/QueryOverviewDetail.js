import React, { useState, useEffect } from 'react';
import { getEnhancedAnalysis, getRecentQueries } from '../services/api';
import './QueryOverviewDetail.css';

/**
 * QueryOverviewDetail Component
 * 
 * This component provides detailed analysis of query execution patterns,
 * performance metrics, and operational insights for automated queries.
 */
const QueryOverviewDetail = () => {
  // =============================================================================
  // STATE MANAGEMENT
  // =============================================================================
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [queries, setQueries] = useState([]);
  const [selectedQuery, setSelectedQuery] = useState(null);
  const [selectedIntent, setSelectedIntent] = useState(null); // { name: 'Commercial', list: Query[] }
  const [filters, setFilters] = useState({
    days: 7,
    engine: null
  });
  const [showInfoGuide, setShowInfoGuide] = useState(false); // Info guide closed by default

  // =============================================================================
  // UTILITY FUNCTIONS
  // =============================================================================
  
  /**
   * Parse text and convert **text** to <strong>text</strong> for bold formatting
   * @param {string} text - Text that may contain **bold** markers
   * @returns {JSX.Element} - Text with bold formatting applied
   */
  const parseBoldText = (text) => {
    if (!text) return null;
    
    // Split text by ** markers and create JSX elements
    const parts = text.split(/(\*\*.*?\*\*)/g);
    
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        // This is bold text, remove ** and wrap in <strong>
        const boldText = part.slice(2, -2);
        return <strong key={index} className="bold-text">{boldText}</strong>;
      }
      return part;
    });
  };

  // =============================================================================
  // CONFIGURATION
  // =============================================================================
  
  const engines = [
    { value: null, label: 'All Engines' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'perplexity', label: 'Perplexity' }
  ];

  const dayOptions = [
    { value: 3, label: 'Last 3 Days' },
    { value: 7, label: 'Last Week' },
    { value: 14, label: 'Last 2 Weeks' },
    { value: 30, label: 'Last Month' }
  ];

  // =============================================================================
  // EFFECTS AND DATA FETCHING
  // =============================================================================
  
  useEffect(() => {
    fetchData();
  }, [filters]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch enhanced analysis data
      const analysisResponse = await getEnhancedAnalysis(filters.days, filters.engine);
      setData(analysisResponse);
      
      // Fetch real query data from database - no limit to show all queries
      const queriesResponse = await getRecentQueries(filters.days, filters.engine);
      setQueries(queriesResponse.queries || []);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleQueryClick = (query) => {
    setSelectedQuery(query);
  };

  const closeQueryDetail = () => {
    setSelectedQuery(null);
  };

  const exportToCSV = () => {
    if (!queries || queries.length === 0) {
      alert('No data to export');
      return;
    }

    // Define CSV headers with all database fields
    const headers = [
      'Date',
      'Query Text',
      'Query Response/Answer',
      'Engine',
      'Model',
      'Response Time (s)',
      'Cost (USD)',
      'Status',
      'Source',
      'Intent',
      'Input Tokens',
      'Output Tokens',
      'Latency (ms)',
      'Raw Excerpt',
      'Extreme Mentioned',
      'Extreme Rank',
      'Is Branded',
      'Created At',
      'Query ID'
    ];

    // Convert data to CSV format
    const csvData = queries.map(query => [
      query.created_at ? new Date(query.created_at).toLocaleDateString() : 'N/A',
      query.query_text || 'N/A',
      query.answer_text || query.raw_excerpt || 'N/A',
      query.engine || 'N/A',
      query.model || 'N/A',
      query.response_time || 'N/A',
      query.cost || 'N/A',
      query.status || 'N/A',
      query.source || 'N/A',
      query.intent || 'N/A',
      query.input_tokens || 'N/A',
      query.output_tokens || 'N/A',
      query.latency_ms || 'N/A',
      query.raw_excerpt ? (query.raw_excerpt.length > 100 ? query.raw_excerpt.substring(0, 100) + '...' : query.raw_excerpt) : 'N/A',
      query.extreme_mentioned ? 'Yes' : 'No',
      query.extreme_rank || 'N/A',
      query.is_branded ? 'Yes' : 'No',
      query.created_at || 'N/A',
      query.id || 'N/A'
    ]);

    // Combine headers and data
    const csvContent = [headers, ...csvData]
      .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
      .join('\n');

    // Create and download CSV file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `query_export_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // =============================================================================
  // CALCULATIONS
  // =============================================================================
  
  const calculateMetrics = () => {
    if (!data || !queries || queries.length === 0) return {};
    
    const totalQueries = queries.length;
    
    const responseTimes = queries.filter(q => q.response_time).map(q => q.response_time);
    const avgResponseTime = responseTimes.length > 0 
      ? (responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length).toFixed(2)
      : 'N/A';
    
    const costs = queries.filter(q => q.cost).map(q => q.cost);
    const avgCost = costs.length > 0 
      ? (costs.reduce((sum, cost) => sum + cost, 0) / costs.length).toFixed(4)
      : 'N/A';
    
    // Calculate engine-specific metrics
    const engineMetrics = queries.reduce((acc, q) => {
      const engine = q.engine || 'unknown';
      if (!acc[engine]) {
        acc[engine] = {
          count: 0,
          totalCost: 0,
          totalResponseTime: 0,
          responseTimes: [],
          costs: []
        };
      }
      acc[engine].count++;
      
      // Handle cost - check if it's a valid number (including 0)
      if (q.cost !== null && q.cost !== undefined && typeof q.cost === 'number') {
        acc[engine].totalCost += q.cost;
        acc[engine].costs.push(q.cost);
      }
      
      // Debug: log cost values for OpenAI runs
      if (engine.includes('gpt') || engine.includes('openai')) {
        console.log(`OpenAI run cost: ${q.cost} (type: ${typeof q.cost})`);
      }
      
      if (q.response_time) {
        acc[engine].totalResponseTime += q.response_time;
        acc[engine].responseTimes.push(q.response_time);
      }
      return acc;
    }, {});
    
    // Calculate averages for each engine
    Object.keys(engineMetrics).forEach(engine => {
      const metrics = engineMetrics[engine];
      if (metrics.responseTimes.length > 0) {
        metrics.avgResponseTime = (metrics.totalResponseTime / metrics.responseTimes.length).toFixed(2);
      } else {
        metrics.avgResponseTime = 'N/A';
      }
      
      // Better cost handling - compute per-1000 cost internally, but render a single $ value
      if (metrics.costs.length > 0) {
        const avgCost = metrics.totalCost / metrics.costs.length;
        const costPer1000 = avgCost * 1000;
        metrics.avgCost = `$${costPer1000.toFixed(2)}`;
      } else {
        metrics.avgCost = '$0.00';
      }
    });
    
    // Intent helpers (4 buckets)
    const transactionalKw = ['buy','price','pricing','purchase','quote','cost','subscription','tier','plan','license'];
    const commercialKw = ['vs','versus','compare','comparison','alternative','alternatives','best','top','review','reviews','benchmark'];
    const navigationalKw = ['login','portal','support','docs','documentation','download','website','homepage','contact'];
    const normalizeIntent = (intent) => {
      if (!intent) return null;
      const i = intent.toLowerCase();
      if (['transactional','commercial','informational','navigational'].includes(i)) {
        return i.charAt(0).toUpperCase() + i.slice(1);
      }
      return null;
    };
    const classifyIntentFromQuery = (q) => {
      const fromField = normalizeIntent(q.intent);
      if (fromField) return fromField;
      const text = (q.query_text || '').toLowerCase();
      const hasAny = (arr) => arr.some(k => text.includes(k));
      if (hasAny(transactionalKw)) return 'Transactional';
      if (hasAny(commercialKw)) return 'Commercial';
      if (hasAny(navigationalKw)) return 'Navigational';
      return 'Informational';
    };

    // Intent distribution across 4 buckets
    const intentDistribution = queries.reduce((acc, q) => {
      const bucket = classifyIntentFromQuery(q);
      acc[bucket] = (acc[bucket] || 0) + 1;
      return acc;
    }, { Transactional: 0, Commercial: 0, Informational: 0, Navigational: 0 });
    
    return {
      totalQueries,
      avgResponseTime,
      avgCost,
      engineMetrics,
      intentDistribution,
      classifyIntentFromQuery
    };
  };

  // =============================================================================
  // LOADING AND ERROR STATES
  // =============================================================================
  
  if (loading) {
    return (
      <div className="query-overview-detail">
        <div className="detail-header">
          <h1>🚀 Query Overview - Detailed Analysis</h1>
          <p>Comprehensive execution patterns and performance metrics</p>
        </div>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading query analysis data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="query-overview-detail">
        <div className="detail-header">
          <h1>🚀 Query Overview - Detailed Analysis</h1>
          <p>Comprehensive execution patterns and performance metrics</p>
        </div>
        <div className="error-container">
          <h3>Error Loading Data</h3>
          <p>{error}</p>
          <button onClick={fetchData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="query-overview-detail">
        <div className="detail-header">
          <h1>🚀 Query Overview - Detailed Analysis</h1>
          <p>Comprehensive execution patterns and performance metrics</p>
        </div>
        <div className="empty-container">
          <h3>No Analysis Available</h3>
          <p>No data found for the selected period.</p>
        </div>
      </div>
    );
  }

  // =============================================================================
  // DATA EXTRACTION
  // =============================================================================
  
  const metrics = calculateMetrics();

  // =============================================================================
  // COMPONENT RENDER
  // =============================================================================
  
  return (
    <div className="query-overview-detail">
      {/* =============================================================================
          PAGE HEADER
          ============================================================================= */}
      <div className="page-header">
        <h1>📊 Query Overview Detail</h1>
        <p>Comprehensive analysis of automated query execution patterns and performance</p>
      </div>

      {/* =============================================================================
          FILTER CONTROLS
          ============================================================================= */}
      <div className="filter-controls">
        <div className="filter-group">
          <label>Time Period:</label>
          <select 
            value={filters.days} 
            onChange={(e) => handleFilterChange('days', parseInt(e.target.value))}
          >
            {dayOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        
        <div className="filter-group">
          <label>Engine:</label>
          <select 
            value={filters.engine || ''} 
            onChange={(e) => handleFilterChange('engine', e.target.value || null)}
          >
            {engines.map(engine => (
              <option key={engine.value || 'all'} value={engine.value || ''}>
                {engine.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* =============================================================================
          INFORMATION GUIDE SECTION
          ============================================================================= */}
      <div className="info-guide-section">
        <div className="info-guide-header">
          <h2>ℹ️ What This Page Shows</h2>
          <button 
            className="info-toggle-btn"
            onClick={() => setShowInfoGuide(!showInfoGuide)}
          >
            {showInfoGuide ? 'Hide Guide' : 'Show Guide'}
          </button>
        </div>
        
        {showInfoGuide && (
          <div className="info-guide-content">
            <div className="guide-section">
              <h3>🎯 Page Purpose</h3>
              <p>
                This page provides a comprehensive view of how your automated competitive intelligence 
                queries are performing. It tracks execution patterns, costs, response times, and 
                engine performance to help you optimize your AI research operations. Queries run automatically 
                at scheduled frequencies, and results are examined over time to identify trends, changes, 
                and opportunities for improvement in your competitive intelligence gathering.
              </p>
            </div>
            
            <div className="guide-section">
              <h3>📈 Key Metrics Explained</h3>
              <div className="metrics-explanation">
                <div className="metric-explanation">
                  <strong>Total Queries:</strong> The total number of automated queries executed in the selected time period.
                </div>
                <div className="metric-explanation">
                  <strong>Success Rate:</strong> Percentage of queries that completed successfully without errors.
                </div>
                <div className="metric-explanation">
                  <strong>Average Response Time:</strong> How long it typically takes for AI engines to respond to your queries (in seconds).
                </div>
                <div className="metric-explanation">
                  <strong>Average Cost:</strong> Displayed as normalized cost per 1000 queries.
                </div>
              </div>
            </div>
            
            <div className="guide-section">
              <h3>🌐 Engine Coverage</h3>
              <p>
                Shows performance breakdown by AI engine (OpenAI, Perplexity, etc.). Each engine displays:
                <br/>• <strong>Queries:</strong> How many queries used this engine
                <br/>• <strong>Avg Response Time:</strong> How fast this engine typically responds
                <br/>• <strong>Avg Cost:</strong> Typical cost per query for this engine
              </p>
            </div>
            
            <div className="guide-section">
              <h3>📊 Query Types Distribution</h3>
              <p>
                Categorizes your queries by intent (Competitor Analysis, Market Research, Brand Monitoring, etc.) 
                to help you understand your research focus areas and identify opportunities for optimization.
              </p>
            </div>
            
            <div className="guide-section">
              <h3>📋 Recent Queries Table</h3>
              <p>
                A detailed list of recent queries with full metadata. Click "View" on any query to see 
                complete details including response text, competitor mentions, and extracted entities.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* =============================================================================
          OVERVIEW SECTION
          ============================================================================= */}
      <div className="overview-section">
        <div className="overview-header">
          <h1>🚀 Query Overview</h1>
          <p>Execution patterns and performance metrics</p>
        </div>
        
        <div className="overview-stats">
          <div className="stat-item">
            <span className="stat-label">TOTAL QUERIES</span>
            <span className="stat-value">{metrics.totalQueries || 0}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">SUCCESS RATE</span>
            <span className="stat-value">
              {queries.length > 0 
                ? `${((queries.filter(q => q.status === 'completed').length / queries.length) * 100).toFixed(1)}%`
                : '0%'
              }
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">AVG RESPONSE TIME</span>
            <span className="stat-value">{metrics.avgResponseTime || 'N/A'}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">AVG COST (PER 1000 QUERIES)</span>
            <span className="stat-value">{metrics.avgCost || '$0.00'}</span>
          </div>
        </div>
      </div>

      {/* =============================================================================
          ENGINE COVERAGE
          ============================================================================= */}
      
      <div className="coverage-section">
        <h2>🌐 Engine Coverage</h2>
        <div className="coverage-grid">
          {Object.entries(metrics.engineMetrics || {}).map(([engine, metrics]) => {
            // Normalize engine names for display
            let displayName = engine;
            let engineIcon = null; // Default no icon
            
            if (engine === 'gpt-4o-mini-search-preview' || engine === 'openai' || engine.startsWith('gpt-')) {
              displayName = 'OpenAI';
              engineIcon = '/icons/chatgpt.png';
            } else if (engine === 'perplexity') {
              displayName = 'Perplexity';
              engineIcon = '/icons/perplexity.png';
            }
            
            return (
              <div key={engine} className="engine-card">
                <div className="engine-header">
                  <h3>
                    {engineIcon && (
                      <img 
                        src={engineIcon} 
                        alt={`${displayName} icon`} 
                        className="engine-icon"
                      />
                    )}
                    {displayName}
                  </h3>
                  <span className="engine-status active">Active</span>
                </div>
                <div className="engine-stats">
                  <div className="stat-item">
                    <span className="stat-label">Queries:</span>
                    <span className="stat-value">{metrics.count}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Avg Response Time:</span>
                    <span className="stat-value">{metrics.avgResponseTime}s</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Avg Cost (per 1000 queries):</span>
                    <span className="stat-value">{metrics.avgCost}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* =============================================================================
          QUERY INTENT DISTRIBUTION (4 buckets)
          ============================================================================= */}
      
      <div className="types-section">
        <h2>📋 Query Intent Distribution</h2>
        <div className="types-grid">
          {Object.entries(metrics.intentDistribution || {}).map(([type, count]) => (
            <div key={type} className="type-card" onClick={() => setSelectedIntent({ name: type, list: queries.filter(q => (metrics.classifyIntentFromQuery ? metrics.classifyIntentFromQuery(q) : 'Informational') === type) })} style={{cursor:'pointer'}}>
              <div className="type-header">
                <h3>{type}</h3>
                <span className="type-count">{count}</span>
              </div>
              <div className="type-percentage">
                {metrics.totalQueries > 0 ? ((count / metrics.totalQueries) * 100).toFixed(1) : 0}%
              </div>
              <div className="type-bar">
                <div 
                  className="type-bar-fill" 
                  style={{
                    width: `${metrics.totalQueries > 0 ? (count / metrics.totalQueries) * 100 : 0}%`
                  }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* =============================================================================
          QUERIES TABLE
          ============================================================================= */}
      
      <div className="queries-section">
        <div className="queries-header">
          <h2>📝 Recent Queries</h2>
          <button 
            className="export-csv-btn"
            onClick={exportToCSV}
            title="Export all query data to CSV"
          >
            📊 Export to CSV
          </button>
        </div>
        <div className="queries-table-container">
          <table className="queries-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Query</th>
                <th>Engine</th>
                <th>Model</th>
                <th>Response Time</th>
                <th>Cost</th>
                <th>Status</th>
                <th>Source</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {queries.map((query, index) => (
                <tr key={query.id || index} className="query-row">
                  <td>{query.created_at ? new Date(query.created_at).toLocaleDateString() : 'N/A'}</td>
                  <td className="query-text">
                    {query.query_text ? 
                      (query.query_text.length > 60 ? 
                        query.query_text.substring(0, 60) + '...' : 
                        query.query_text
                      ) : 
                      'N/A'
                    }
                  </td>
                  <td>
                    <span className={`engine-badge ${query.engine || 'unknown'}`}>
                      {query.engine || 'Unknown'}
                    </span>
                  </td>
                  <td>{query.model || 'N/A'}</td>
                  <td>{query.response_time ? `${query.response_time}s` : 'N/A'}</td>
                  <td>{query.cost ? `$${query.cost.toFixed(4)}` : 'N/A'}</td>
                  <td>
                    <span className={`status-badge ${query.status || 'completed'}`}>
                      {query.status || 'Completed'}
                    </span>
                  </td>
                  <td>
                    <span className={`source-badge ${query.source || 'manual'}`}>
                      {query.source || 'Manual'}
                    </span>
                  </td>
                  <td>
                    <button 
                      className="view-details-btn"
                      onClick={() => handleQueryClick(query)}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* =============================================================================
          QUERY DETAIL MODAL
          ============================================================================= */}
      {selectedQuery && (
        <div className="modal-overlay" onClick={() => setSelectedQuery(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Query Details</h2>
              <button 
                className="modal-close"
                onClick={() => setSelectedQuery(null)}
              >
                ✕
              </button>
            </div>
            
            <div className="modal-section">
              <h3>📝 Query Information</h3>
              <div className="modal-info-grid">
                <div className="info-item">
                  <span className="info-label">Query:</span>
                  <span className="info-value">{selectedQuery.query_text}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Status:</span>
                  <span className={`modal-badge status`}>{selectedQuery.status}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Source:</span>
                  <span className={`modal-badge source`}>{selectedQuery.source}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Intent:</span>
                  <span className={`modal-badge intent`}>{selectedQuery.intent || 'N/A'}</span>
                </div>
              </div>
            </div>

            <div className="modal-section">
              <h3>⚡ Performance Metrics</h3>
              <div className="modal-metrics-grid">
                <div className="metric-card">
                  <div className="metric-icon">🔧</div>
                  <div className="metric-content">
                    <div className="metric-label">Engine</div>
                    <div className="metric-value">{selectedQuery.engine}</div>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon">🤖</div>
                  <div className="metric-content">
                    <div className="metric-label">Model</div>
                    <div className="metric-value">{selectedQuery.model || 'N/A'}</div>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon">⏱️</div>
                  <div className="metric-content">
                    <div className="metric-label">Response Time</div>
                    <div className="metric-value">
                      {selectedQuery.response_time ? `${selectedQuery.response_time.toFixed(2)}s` : 'N/A'}
                    </div>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon">💰</div>
                  <div className="metric-content">
                    <div className="metric-label">Cost</div>
                    <div className="metric-value">${selectedQuery.cost?.toFixed(4) || '0.0000'}</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-section">
              <h3>🔢 Token Usage</h3>
              <div className="modal-metrics-grid">
                <div className="metric-card">
                  <div className="metric-icon">📥</div>
                  <div className="metric-content">
                    <div className="metric-label">Input</div>
                    <div className="metric-value">{selectedQuery.input_tokens || 0}</div>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon">📤</div>
                  <div className="metric-content">
                    <div className="metric-label">Output</div>
                    <div className="metric-value">{selectedQuery.output_tokens || 0}</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-section">
              <h3>🎯 Competitive Intelligence</h3>
              <div className="modal-metrics-grid">
                <div className="metric-card">
                  <div className="metric-icon">🏢</div>
                  <div className="metric-content">
                    <div className="metric-label">Extreme Networks</div>
                    <div className="metric-value">
                      {selectedQuery.extreme_mentioned ? '✅ Mentioned' : '❌ Not Mentioned'}
                    </div>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon">🔗</div>
                  <div className="metric-content">
                    <div className="metric-label">Citations</div>
                    <div className="metric-value">{selectedQuery.total_citations || 0}</div>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon">👥</div>
                  <div className="metric-content">
                    <div className="metric-label">Entities</div>
                    <div className="metric-value">{selectedQuery.total_entities || 0}</div>
                  </div>
                </div>
              </div>
            </div>

            {selectedQuery.answer_text && (
              <div className="modal-section">
                <h3>💬 Response Text</h3>
                <div className="response-text-container">
                  {parseBoldText(selectedQuery.answer_text)}
                </div>
              </div>
            )}

            {selectedQuery.competitor_mentions && Object.keys(selectedQuery.competitor_mentions).length > 0 && (
              <div className="modal-section">
                <h3>🏆 Competitor Mentions</h3>
                <div className="tags-container">
                  {Object.entries(selectedQuery.competitor_mentions).map(([competitor, count]) => (
                    <span key={competitor} className="tag-item">
                      <span className="tag-name">{competitor}</span>
                      <span className="tag-count">{count}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {selectedQuery.domains && selectedQuery.domains.length > 0 && (
              <div className="modal-section">
                <h3>🌐 Domains Found</h3>
                <div className="tags-container">
                  {selectedQuery.domains.map((domain, index) => (
                    <span key={index} className="tag-item domain">
                      {domain}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {selectedIntent && (
        <div className="modal-overlay" onClick={() => setSelectedIntent(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">{selectedIntent.name} Queries</h2>
              <button 
                className="modal-close"
                onClick={() => setSelectedIntent(null)}
              >
                ✕
              </button>
            </div>

            <div className="queries-table-container">
              <table className="queries-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Query</th>
                    <th>Engine</th>
                    <th>Model</th>
                    <th>Response Time</th>
                    <th>Cost</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {(selectedIntent.list || []).map((query, index) => (
                    <tr key={query.id || index} className="query-row">
                      <td>{query.created_at ? new Date(query.created_at).toLocaleDateString() : 'N/A'}</td>
                      <td className="query-text">
                        {query.query_text ? 
                          (query.query_text.length > 60 ? 
                            query.query_text.substring(0, 60) + '...' : 
                            query.query_text
                          ) : 
                          'N/A'
                        }
                      </td>
                      <td>
                        <span className={`engine-badge ${query.engine || 'unknown'}`}>
                          {query.engine || 'Unknown'}
                        </span>
                      </td>
                      <td>{query.model || 'N/A'}</td>
                      <td>{query.response_time ? `${query.response_time}s` : 'N/A'}</td>
                      <td>{query.cost ? `$${query.cost.toFixed(4)}` : 'N/A'}</td>
                      <td>
                        <span className={`status-badge ${query.status || 'completed'}`}>
                          {query.status || 'Completed'}
                        </span>
                      </td>
                      <td>
                        <button 
                          className="view-details-btn"
                          onClick={() => setSelectedQuery(query)}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* =============================================================================
          BACK TO DASHBOARD
          ============================================================================= */}
      
      <div className="back-section">
        <a href="/metrics" className="back-link">
          ← Back to Metrics Dashboard
        </a>
      </div>
      
    </div>
  );
};

export default QueryOverviewDetail;
