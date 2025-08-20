import React, { useState, useEffect } from 'react';
import { getEnhancedAnalysis } from '../services/api';
import './EnhancedMetricsDashboard.css';

const EnhancedMetricsDashboard = () => {
  const [analysis, setAnalysis] = useState(null);
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
    fetchAnalysis();
  }, [filters]);

  const fetchAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getEnhancedAnalysis(filters.days, filters.engine);
      setAnalysis(data);
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
      <div className="enhanced-metrics-loading">
        <div className="loading-spinner"></div>
        <p>Loading enhanced analysis...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="enhanced-metrics-error">
        <h3>Error Loading Analysis</h3>
        <p>{error}</p>
        <button onClick={fetchAnalysis} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  if (!analysis || !analysis.analysis) {
    return (
      <div className="enhanced-metrics-empty">
        <h3>No Analysis Available</h3>
        <p>No data found for the selected period.</p>
      </div>
    );
  }

  const { citations, competitors } = analysis.analysis;

  return (
    <div className="enhanced-metrics-dashboard">
      <div className="dashboard-header">
        <h2>Enhanced Competitive Intelligence Dashboard</h2>
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
          <span>Analyzing {analysis.total_runs_analyzed} runs</span>
          <span>Period: {analysis.start_date} to {analysis.end_date}</span>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Citation Analysis Section */}
        <div className="dashboard-section citation-analysis">
          <h3>📊 Citation Analysis</h3>
          
          <div className="metrics-overview">
            <div className="metric-card">
              <div className="metric-value">{citations.total_citations || 0}</div>
              <div className="metric-label">Total Citations</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{citations.unique_domains || 0}</div>
              <div className="metric-label">Unique Domains</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{citations.avg_quality_score || 0}</div>
              <div className="metric-label">Avg Quality Score</div>
            </div>
          </div>

          {/* Top 5 Most Mentioned Websites */}
          <div className="analysis-subsection">
            <h4>🏆 Top 5 Most Mentioned Websites</h4>
            <div className="top-websites">
              {citations.top_5_websites_by_mentions?.map((website, index) => (
                <div key={website.domain} className="website-card">
                  <div className="website-rank">#{index + 1}</div>
                  <div className="website-info">
                    <div className="website-domain">{website.domain}</div>
                    <div className="website-stats">
                      <span className="stat">
                        📍 {website.total_mentions} total mentions
                      </span>
                      <span className="stat">
                        🎯 {website.avg_quality} avg quality
                      </span>
                      <span className="stat">
                        📊 {website.avg_rank} avg rank
                      </span>
                    </div>
                  </div>
                </div>
              )) || <p>No website data available</p>}
            </div>
          </div>

          {/* Citation Quality Distribution */}
          <div className="analysis-subsection">
            <h4>📈 Citation Quality Distribution</h4>
            <div className="quality-distribution">
              {citations.quality_distribution && Object.entries(citations.quality_distribution).map(([quality, count]) => (
                <div key={quality} className="quality-bar">
                  <div className="quality-label">{quality.charAt(0).toUpperCase() + quality.slice(1)}</div>
                  <div className="quality-bar-container">
                    <div 
                      className="quality-bar-fill" 
                      style={{ 
                        width: `${(count / Math.max(...Object.values(citations.quality_distribution))) * 100}%`,
                        backgroundColor: getQualityColor(quality)
                      }}
                    ></div>
                  </div>
                  <div className="quality-count">{count}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Competitor Analysis Section */}
        <div className="dashboard-section competitor-analysis">
          <h3>🎯 Competitor Analysis</h3>
          
          <div className="metrics-overview">
            <div className="metric-card">
              <div className="metric-value">{competitors.total_entity_mentions || 0}</div>
              <div className="metric-label">Total Entity Mentions</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{competitors.unique_entities || 0}</div>
              <div className="metric-label">Unique Entities</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">
                {competitors.detection_effectiveness?.entity_extraction_rate || 0}%
              </div>
              <div className="metric-label">Extraction Rate</div>
            </div>
          </div>

          {/* Top Competitors */}
          <div className="analysis-subsection">
            <h4>🥇 Top Competitors by Mentions</h4>
            <div className="top-competitors">
              {competitors.top_competitors?.map((competitor, index) => (
                <div key={competitor.name} className="competitor-card">
                  <div className="competitor-rank">#{index + 1}</div>
                  <div className="competitor-info">
                    <div className="competitor-name">{competitor.name}</div>
                    <div className="competitor-stats">
                      <span className="stat">
                        📍 {competitor.mentions} mentions
                      </span>
                      <span className="stat">
                        🎯 {competitor.avg_rank} avg rank
                      </span>
                    </div>
                  </div>
                </div>
              )) || <p>No competitor data available</p>}
            </div>
          </div>

          {/* Extreme Networks Analysis */}
          <div className="analysis-subsection">
            <h4>🔍 Extreme Networks Analysis</h4>
            {competitors.extreme_networks_detailed_analysis && (
              <div className="extreme-networks-analysis">
                <div className="en-metrics">
                  <div className="en-metric">
                    <div className="en-value">{competitors.extreme_networks_detailed_analysis.total_mentions}</div>
                    <div className="en-label">Total Mentions</div>
                  </div>
                  <div className="en-metric">
                    <div className="en-value">{competitors.extreme_networks_detailed_analysis.runs_mentioned}</div>
                    <div className="en-label">Runs Mentioned</div>
                  </div>
                  <div className="en-metric">
                    <div className="en-value">
                      {competitors.detection_effectiveness?.extreme_networks_detection_rate || 0}%
                    </div>
                    <div className="en-label">Detection Rate</div>
                  </div>
                </div>

                {/* Ranking Analysis */}
                {competitors.extreme_networks_detailed_analysis.ranking_analysis?.length > 0 && (
                  <div className="en-ranking-analysis">
                    <h5>Ranking Analysis</h5>
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
        </div>
      </div>
    </div>
  );
};

// Helper function to get quality colors
const getQualityColor = (quality) => {
  switch (quality) {
    case 'excellent': return '#10b981';
    case 'good': return '#3b82f6';
    case 'fair': return '#f59e0b';
    case 'poor': return '#ef4444';
    default: return '#6b7280';
  }
};

export default EnhancedMetricsDashboard;
