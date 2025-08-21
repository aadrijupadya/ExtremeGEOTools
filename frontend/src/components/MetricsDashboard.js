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
          <div className="stat-icon">🎯</div>
          <div className="stat-content">
            <h3>{competitors?.top_competitors?.length || 0}</h3>
            <p>Competitors Tracked</p>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">🔗</div>
          <div className="stat-content">
            <h3>{citations?.total_citations || 0}</h3>
            <p>Citations Found</p>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">🌐</div>
          <div className="stat-content">
            <h3>{citations?.unique_domains || 0}</h3>
            <p>Unique Sources</p>
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
              <span className="metric-label">Success Rate:</span>
              <span className="metric-value">
                {totalRuns > 0 
                  ? `${((totalRuns - (data?.analysis?.failed_runs || 0)) / totalRuns * 100).toFixed(1)}%`
                  : '0%'
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
              <span className="metric-label">Avg Cost per Query:</span>
              <span className="metric-value">
                {data?.analysis?.avg_cost_per_query 
                  ? `$${data.analysis.avg_cost_per_query.toFixed(4)}`
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
              <span className="metric-label"># Main Competitors:</span>
              <span className="metric-value">{competitors?.top_competitors?.length || 0}</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Top Competitor:</span>
              <span className="metric-value">
                {competitors?.top_competitors?.[0]?.name || 'N/A'}
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
              <span className="metric-label">Brand Mentions:</span>
              <span className="metric-value">
                {data?.analysis?.competitors?.extreme_networks_mentions || 0}
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Share of Voice:</span>
              <span className="metric-value">
                {data?.analysis?.competitors?.extreme_networks_detection_rate 
                  ? `${(data.analysis.competitors.extreme_networks_detection_rate * 100).toFixed(1)}%`
                  : 'N/A'
                }
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Avg Rank:</span>
              <span className="metric-value">
                {data?.analysis?.competitors?.extreme_networks_avg_rank 
                  ? data.analysis.competitors.extreme_networks_avg_rank.toFixed(1)
                  : 'N/A'
                }
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Market Position:</span>
              <span className="metric-value">
                {data?.analysis?.competitors?.extreme_networks_avg_rank 
                  ? (data.analysis.competitors.extreme_networks_avg_rank <= 3 ? 'Strong' : 
                     data.analysis.competitors.extreme_networks_avg_rank <= 5 ? 'Good' : 'Developing')
                  : 'N/A'
                }
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
              <span className="metric-label">Avg Domain Quality:</span>
              <span className="metric-value">
                {citations?.avg_domain_quality 
                  ? `${citations.avg_domain_quality.toFixed(1)}/10`
                  : 'N/A'
                }
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Top Domain:</span>
              <span className="metric-value">
                {citations?.top_domains?.[0]?.domain || 'N/A'}
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

      {/* =============================================================================
          QUICK INSIGHTS SECTION
          ============================================================================= */}
      
      <div className="quick-insights">
        <h2>💡 Quick Insights</h2>
        <div className="insights-grid">
          <div className="insight-item">
            <span className="insight-icon">📈</span>
            <p>
              {totalRuns > 0 
                ? `Analyzed ${totalRuns} queries over the last ${filters.days} days`
                : 'No queries analyzed in the selected period'
              }
            </p>
          </div>
          <div className="insight-item">
            <span className="insight-icon">🎯</span>
            <p>
              {data?.analysis?.competitors?.extreme_networks_mentions > 0
                ? `Extreme Networks mentioned in ${data.analysis.competitors.extreme_networks_mentions} queries`
                : 'Extreme Networks brand monitoring active'
              }
            </p>
          </div>
          <div className="insight-item">
            <span className="insight-icon">🔍</span>
            <p>
              {citations?.total_citations > 0
                ? `Found ${citations.total_citations} citations from ${citations.unique_domains || 0} sources`
                : 'Citation analysis in progress'
              }
            </p>
          </div>
        </div>
      </div>

      {/* =============================================================================
          RECENT ACTIVITY
          ============================================================================= */}
      
      <div className="recent-activity">
        <h2>🕒 Recent Activity</h2>
        <div className="activity-list">
          {totalRuns > 0 ? (
            <>
              <div className="activity-item">
                <span className="activity-time">Latest</span>
                <span className="activity-text">
                  {data?.analysis?.competitors?.top_competitors?.[0]?.name 
                    ? `Top competitor: ${data.analysis.competitors.top_competitors[0].name}`
                    : 'Competitor analysis completed'
                  }
                </span>
              </div>
              <div className="activity-item">
                <span className="activity-time">Performance</span>
                <span className="activity-text">
                  {data?.analysis?.avg_response_time 
                    ? `Average response time: ${data.analysis.avg_response_time.toFixed(1)}s`
                    : 'Response time tracking active'
                  }
                </span>
              </div>
              <div className="activity-item">
                <span className="activity-time">Costs</span>
                <span className="activity-text">
                  {data?.analysis?.avg_cost_per_query 
                    ? `Average cost per query: $${data.analysis.avg_cost_per_query.toFixed(4)}`
                    : 'Cost tracking active'
                  }
                </span>
              </div>
            </>
          ) : (
            <div className="activity-item">
              <span className="activity-time">Status</span>
              <span className="activity-text">No automated queries found in the selected period</span>
            </div>
          )}
        </div>
      </div>
      
    </div>
  );
};

export default MetricsDashboard;
