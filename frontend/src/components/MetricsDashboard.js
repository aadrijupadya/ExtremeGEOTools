import React, { useState, useEffect } from 'react';
import { getEnhancedAnalysis } from '../services/api';
import './MetricsDashboard.css';

/**
 * MetricsDashboard Component
 * 
 * This is the main metrics page that provides an overview of automated query results
 * with 4 main components: Query Overview, Competitor Analysis, Extreme Focus, and Citation Analysis.
 * Each component shows summary data and links to detailed endpoints for deeper analysis.
 */
const MetricsDashboard = () => {
  // =============================================================================
  // STATE MANAGEMENT
  // =============================================================================
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    days: 7,
    engine: null
  });

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
      const response = await getEnhancedAnalysis(filters.days, filters.engine);
      setData(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  // =============================================================================
  // LOADING AND ERROR STATES
  // =============================================================================
  
  if (loading) {
    return (
      <div className="metrics-dashboard">
        <div className="dashboard-header">
          <h1>Metrics Dashboard</h1>
          <p className="section-description">
            Comprehensive analysis of automated query results, competitor mentions, and Extreme Networks visibility.
          </p>
        </div>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading automated query results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="metrics-dashboard">
        <div className="dashboard-header">
          <h1>Metrics Dashboard</h1>
          <p className="section-description">
            Comprehensive analysis of automated query results, competitor mentions, and Extreme Networks visibility.
          </p>
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

  if (!data || !data.analysis) {
    return (
      <div className="metrics-dashboard">
        <div className="dashboard-header">
          <h1>Metrics Dashboard</h1>
          <p className="section-description">
            Comprehensive analysis of automated query results, competitor mentions, and Extreme Networks visibility.
          </p>
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
  
  const { citations, competitors } = data.analysis;
  const totalRuns = data.total_runs_analyzed || 0;
  
  // Calculate Extreme mentions from competitor analysis
  const extremeMentions = competitors?.extreme_networks_detailed_analysis?.total_mentions || 0;
  const extremeMentionRate = totalRuns > 0 ? ((extremeMentions / totalRuns) * 100).toFixed(1) : '0';
  
  // Get citation analysis data
  const topDomain = citations?.domain_breakdown?.most_frequent_domain || 'N/A';
  const topSource = citations?.top_5_domains_by_frequency?.[0]?.domain || 'N/A';

  // =============================================================================
  // COMPONENT RENDER
  // =============================================================================
  
  return (
    <div className="metrics-dashboard">
      
      {/* =============================================================================
          DASHBOARD HEADER
          ============================================================================= */}
      
      <div className="dashboard-header">
        <h1>Metrics Dashboard</h1>
        <p className="section-description">
          Comprehensive analysis of automated query results, competitor mentions, and Extreme Networks visibility.
        </p>
        
        {/* Filter Controls */}
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
          
          <div className="engine-status">
            <strong>You are now seeing results for:</strong>
            <div className="engine-display">
              {filters.engine === 'openai' ? (
                <span className="engine-logo">
                  <img src="/icons/chatgpt.png" alt="OpenAI" className="engine-icon" />
                  OpenAI
                </span>
              ) : filters.engine === 'perplexity' ? (
                <span className="engine-logo">
                  <img src="/icons/perplexity.png" alt="Perplexity" className="engine-icon" />
                  Perplexity
                </span>
              ) : (
                <span className="engine-logo">
                  All Engines
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* =============================================================================
          OVERVIEW STATS
          ============================================================================= */}
      
      <div className="overview-stats">
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <h3>{totalRuns}</h3>
            <p>Total Runs Analyzed</p>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">⭐</div>
          <div className="stat-content">
            <h3>{extremeMentions}</h3>
            <p>Extreme Mentions</p>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">🔗</div>
          <div className="stat-content">
            <h3>{citations?.total_citations || 0}</h3>
            <p>Total Citations</p>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">🎯</div>
          <div className="stat-content">
            <h3>{competitors?.top_competitors?.length || 0}</h3>
            <p>Competitors Found</p>
          </div>
        </div>
      </div>

      {/* =============================================================================
          MAIN COMPONENTS GRID
          ============================================================================= */}
      
      <div className="components-grid">
        
        {/* =============================================================================
            QUERY OVERVIEW COMPONENT
            ============================================================================= */}
        
        <div className="component-card query-overview">
          <div className="component-header">
            <h2>🚀 Query Overview</h2>
            <p>Execution patterns and performance metrics</p>
          </div>
          
          <div className="component-content">
            <div className="metric-row">
              <span className="metric-label">Total Queries:</span>
              <span className="metric-value">{totalRuns}</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Engine Split:</span>
              <span className="metric-value">
                {data?.analysis?.engine_breakdown?.openai && data?.analysis?.engine_breakdown?.perplexity
                  ? `${data.analysis.engine_breakdown.openai} OpenAI, ${data.analysis.engine_breakdown.perplexity} Perplexity`
                  : 'Mixed'
                }
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Avg Response Time:</span>
              <span className="metric-value">
                {data?.analysis?.avg_response_time 
                  ? `${data.analysis.avg_response_time.toFixed(1)}s`
                  : 'N/A'
                }
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Total Cost:</span>
              <span className="metric-value">
                {data?.analysis?.total_cost 
                  ? `$${data.analysis.total_cost.toFixed(2)}`
                  : 'N/A'
                }
              </span>
            </div>
          </div>
          
          <div className="component-footer">
            <a href="/metrics/query-overview" className="detail-link">
              View Detailed Analysis →
            </a>
          </div>
        </div>

        {/* =============================================================================
            COMPETITOR ANALYSIS COMPONENT
            ============================================================================= */}
        
        <div className="component-card competitor-analysis">
          <div className="component-header">
            <h2>🎯 Competitor Analysis</h2>
            <p>Market positioning and competitive landscape</p>
          </div>
          
          <div className="component-content">
            <div className="metric-row">
              <span className="metric-label">Total Competitors:</span>
              <span className="metric-value">{competitors?.top_competitors?.length || 0}</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Top Competitor:</span>
              <span className="metric-value">
                {competitors?.top_competitors?.[0]?.name || 'N/A'}
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Entity Mentions:</span>
              <span className="metric-value">
                {competitors?.total_entity_mentions || 0}
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Detection Rate:</span>
              <span className="metric-value">
                {competitors?.detection_effectiveness?.entity_extraction_rate 
                  ? `${competitors.detection_effectiveness.entity_extraction_rate.toFixed(1)}%`
                  : 'N/A'
                }
              </span>
            </div>
          </div>
          
          <div className="component-footer">
            <a href="/metrics/competitor-analysis" className="detail-link">
              View Detailed Analysis →
            </a>
          </div>
        </div>

        {/* =============================================================================
            EXTREME FOCUS COMPONENT
            ============================================================================= */}
        
        <div className="component-card extreme-focus">
          <div className="component-header">
            <h2>⭐ Extreme Focus</h2>
            <p>Brand visibility and market positioning</p>
          </div>
          
          <div className="component-content">
            <div className="metric-row">
              <span className="metric-label">Total Mentions:</span>
              <span className="metric-value">
                {extremeMentions}
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Mention Rate:</span>
              <span className="metric-value">
                {extremeMentionRate}%
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Coverage Gaps:</span>
              <span className="metric-value">
                {data?.analysis?.coverage_gaps?.total_gaps || 0}
              </span>
            </div>
          </div>
          
          <div className="component-footer">
            <a href="/metrics/extreme-focus" className="detail-link">
              View Detailed Analysis →
            </a>
          </div>
        </div>

        {/* =============================================================================
            CITATION ANALYSIS COMPONENT
            ============================================================================= */}
        
        <div className="component-card citation-analysis">
          <div className="component-header">
            <h2>🔗 Citation Analysis</h2>
            <p>Source quality and information credibility</p>
          </div>
          
          <div className="component-content">
            <div className="metric-row">
              <span className="metric-label">Total Citations:</span>
              <span className="metric-value">{citations?.total_citations || 0}</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Unique Sources:</span>
              <span className="metric-value">{citations?.unique_domains || 0}</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Top Domain:</span>
              <span className="metric-value">
                {topDomain}
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Top Source:</span>
              <span className="metric-value">
                {topSource}
              </span>
            </div>
          </div>
          
          <div className="component-footer">
            <a href="/metrics/citation-analysis" className="detail-link">
              View Detailed Analysis →
            </a>
          </div>
        </div>
      </div>


      
    </div>
  );
};

export default MetricsDashboard;
