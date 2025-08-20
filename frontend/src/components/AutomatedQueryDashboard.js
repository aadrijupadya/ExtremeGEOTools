import React, { useState, useEffect } from 'react';
import { getEnhancedAnalysis } from '../services/api';
import './AutomatedQueryDashboard.css';

const AutomatedQueryDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    days: 7,
    engine: null
  });

  const engines = [
    { value: null, label: 'All Engines' },
    { value: 'gpt-4o-mini-search-preview', label: 'OpenAI GPT-4o' },
    { value: 'perplexity', label: 'Perplexity' }
  ];

  const dayOptions = [
    { value: 3, label: 'Last 3 Days' },
    { value: 7, label: 'Last Week' },
    { value: 14, label: 'Last 2 Weeks' },
    { value: 30, label: 'Last Month' }
  ];

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

  if (loading) {
    return (
      <div className="automated-dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading automated query results...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="automated-dashboard-error">
        <h3>Error Loading Data</h3>
        <p>{error}</p>
        <button onClick={fetchData} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  if (!data || !data.analysis) {
    return (
      <div className="automated-dashboard-empty">
        <h3>No Analysis Available</h3>
        <p>No data found for the selected period.</p>
        <pre className="debug-info">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    );
  }

  const { citations, competitors } = data.analysis;

  // Debug logging
  console.log('Analysis data:', data);
  console.log('Citations:', citations);
  console.log('Competitors:', competitors);

  // Ensure citations and competitors exist
  if (!citations || !competitors) {
    return (
      <div className="automated-dashboard-error">
        <h3>Data Structure Error</h3>
        <p>Expected citations and competitors data not found.</p>
        <pre className="debug-info">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    );
  }

  return (
    <div className="automated-query-dashboard">
      <div className="dashboard-header">
        <h2>🤖 Automated Query Results Dashboard</h2>
        <div className="dashboard-filters">
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
        <div className="analysis-summary">
          <span>📊 Analyzing {data.total_runs_analyzed} {data.run_source === 'automated' ? 'automated' : 'enterprise networking'} runs</span>
          <span>📅 Period: {data.start_date.split('T')[0]} to {data.end_date.split('T')[0]}</span>
          {data.run_source === 'enterprise_networking_fallback' && (
            <span className="fallback-notice">⚠️ Using enterprise networking query fallback</span>
          )}
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Query Overview Section */}
        <div className="dashboard-section overview-section">
          <h3>📈 Query Overview</h3>
          
          <div className="overview-metrics">
            <div className="metric-card primary">
              <div className="metric-value">{data.total_runs_analyzed}</div>
              <div className="metric-label">Total Automated Runs</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{citations.total_citations || 0}</div>
              <div className="metric-label">Total Citations Found</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{competitors.total_entity_mentions || 0}</div>
              <div className="metric-label">Competitor Mentions</div>
            </div>
          </div>

          {/* Recent Queries List */}
          <div className="recent-queries">
            <h4>🔍 Recent Automated Queries</h4>
            <div className="queries-list">
              {Object.entries(competitors.competitor_detection_analysis?.competitor_mentions_by_run || {})
                .slice(0, 5)
                .map(([runId, runData]) => (
                  <div key={runId} className="query-item">
                    <div className="query-content">
                      <div className="query-text">{runData.query}</div>
                      <div className="query-meta">
                        <span className="engine-tag">{runData.engine}</span>
                        <span className="entities-count">
                          {runData.total_entities} entities found
                        </span>
                      </div>
                    </div>
                    <div className="query-status">
                      {runData.extreme_mentioned ? (
                        <span className="status-badge extreme">Extreme Networks Mentioned</span>
                      ) : (
                        <span className="status-badge none">No Extreme Networks</span>
                      )}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>

        {/* Competitor Analysis Section */}
        <div className="dashboard-section competitor-section">
          <h3>🏆 Competitor Analysis</h3>
          
          <div className="competitor-metrics">
            <div className="metric-card">
              <div className="metric-value">{competitors.unique_entities || 0}</div>
              <div className="metric-label">Unique Competitors</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">
                {competitors.detection_effectiveness?.entity_extraction_rate || 0}%
              </div>
              <div className="metric-label">Entity Detection Rate</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">
                {competitors.detection_effectiveness?.extreme_networks_detection_rate || 0}%
              </div>
              <div className="metric-label">Extreme Networks Detection</div>
            </div>
          </div>

          {/* Top Competitors */}
          <div className="top-competitors">
            <h4>🥇 Top Competitors by Mentions</h4>
            <div className="competitors-list">
              {competitors.top_competitors?.map((competitor, index) => (
                <div key={competitor.name} className="competitor-item">
                  <div className="competitor-rank">#{index + 1}</div>
                  <div className="competitor-info">
                    <div className="competitor-name">{competitor.name}</div>
                    <div className="competitor-stats">
                      <span className="stat mentions">
                        📍 {competitor.mentions} mentions
                      </span>
                      {competitor.avg_rank !== "N/A" && (
                        <span className="stat rank">
                          🎯 Rank {competitor.avg_rank}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )) || <p>No competitor data available</p>}
            </div>
          </div>
        </div>

        {/* Extreme Networks Focus Section */}
        <div className="dashboard-section extreme-section">
          <h3>🔍 Extreme Networks Focus</h3>
          
          {competitors.extreme_networks_detailed_analysis && (
            <div className="extreme-analysis">
              <div className="extreme-metrics">
                <div className="extreme-metric">
                  <div className="extreme-value">{competitors.extreme_networks_detailed_analysis.total_mentions}</div>
                  <div className="extreme-label">Total Mentions</div>
                </div>
                <div className="extreme-metric">
                  <div className="extreme-value">{competitors.extreme_networks_detailed_analysis.runs_mentioned}</div>
                  <div className="extreme-label">Runs Mentioned</div>
                </div>
                <div className="extreme-metric">
                  <div className="extreme-value">
                    {competitors.detection_effectiveness?.extreme_networks_mention_rate || 0}%
                  </div>
                  <div className="extreme-label">Mention Rate</div>
                </div>
              </div>

              {/* Ranking Analysis */}
              {competitors.extreme_networks_detailed_analysis.ranking_analysis?.length > 0 && (
                <div className="ranking-analysis">
                  <h4>📊 Ranking Analysis</h4>
                  <div className="ranking-list">
                    {competitors.extreme_networks_detailed_analysis.ranking_analysis.map((rank, index) => (
                      <div key={index} className="ranking-item">
                        <div className="rank-position">#{rank.rank}</div>
                        <div className="rank-details">
                          <div className="rank-query">{rank.query}</div>
                          <div className="rank-meta">
                            {rank.engine} • {rank.date} • {rank.total_entities_in_run} entities
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Citation Analysis Section */}
        <div className="dashboard-section citation-section">
          <h3>📚 Citation Analysis</h3>
          
          <div className="citation-metrics">
            <div className="metric-card">
              <div className="metric-value">{citations.unique_domains || 0}</div>
              <div className="metric-label">Unique Domains</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{citations.total_citations || 0}</div>
              <div className="metric-label">Total Citations</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">
                {citations.domain_breakdown?.domains_with_multiple_mentions || 0}
              </div>
              <div className="metric-label">Multi-Mention Domains</div>
            </div>
          </div>

          {/* Top 5 Domains by Frequency */}
          <div className="analysis-subsection">
            <h4>🏆 Top 5 Domains by Frequency</h4>
            <div className="top-domains">
              {citations.top_5_domains_by_frequency?.map((domain, index) => (
                <div key={domain.domain} className="domain-card">
                  <div className="domain-rank">#{index + 1}</div>
                  <div className="domain-info">
                    <div className="domain-name">{domain.domain}</div>
                    <div className="domain-stats">
                      <span className="stat">
                        📍 {domain.total_mentions} total mentions
                      </span>
                      <span className="stat">
                        🔗 {domain.unique_urls} unique URLs
                      </span>
                      <span className="stat">
                        📊 {domain.runs_mentioned} runs mentioned
                      </span>
                      <span className="stat">
                        🎯 {domain.avg_rank} avg rank
                      </span>
                    </div>
                    {domain.sample_urls && domain.sample_urls.length > 0 && (
                      <div className="sample-urls">
                        <span className="url-label">Sample URLs:</span>
                        {domain.sample_urls.map((url, urlIndex) => (
                          <a 
                            key={urlIndex} 
                            href={url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="sample-url"
                          >
                            {url.length > 50 ? url.substring(0, 50) + '...' : url}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )) || <p>No domain data available</p>}
            </div>
          </div>

          {/* Domain Breakdown Summary */}
          {citations.domain_breakdown && (
            <div className="analysis-subsection">
              <h4>📈 Domain Breakdown</h4>
              <div className="domain-summary">
                <div className="summary-item">
                  <span className="summary-label">Total Domains Found:</span>
                  <span className="summary-value">{citations.domain_breakdown.total_domains_found}</span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Domains with Multiple Mentions:</span>
                  <span className="summary-value">{citations.domain_breakdown.domains_with_multiple_mentions}</span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Most Frequent Domain:</span>
                  <span className="summary-value highlight">{citations.domain_breakdown.most_frequent_domain}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AutomatedQueryDashboard;
