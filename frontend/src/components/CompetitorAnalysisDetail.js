import React, { useState, useEffect } from 'react';
import { getEnhancedAnalysis } from '../services/api';
import './CompetitorAnalysisDetail.css';

/**
 * CompetitorAnalysisDetail Component
 * 
 * This component provides detailed analysis of competitor mentions,
 * market positioning, and competitive landscape insights.
 */
const CompetitorAnalysisDetail = () => {
  // =============================================================================
  // STATE MANAGEMENT
  // =============================================================================
  
  // Helper functions for filter persistence
  const getStoredFilters = () => {
    try {
      const stored = localStorage.getItem('competitorAnalysisFilters');
      if (stored) {
        const parsed = JSON.parse(stored);
        // Validate the stored values
        const validDays = [3, 7, 14, 30].includes(parsed.days) ? parsed.days : 7;
        const validEngine = ['openai', 'perplexity', null].includes(parsed.engine) ? parsed.engine : null;
        return { days: validDays, engine: validEngine };
      }
    } catch (error) {
      console.warn('Failed to parse stored filters:', error);
    }
    return { days: 7, engine: null };
  };

  const saveFilters = (newFilters) => {
    try {
      localStorage.setItem('competitorAnalysisFilters', JSON.stringify(newFilters));
    } catch (error) {
      console.warn('Failed to save filters:', error);
    }
  };
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState(getStoredFilters());
  const [showInfoGuide, setShowInfoGuide] = useState(true); // New state for info guide visibility

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
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    saveFilters(newFilters);
  };

  // =============================================================================
  // LOADING AND ERROR STATES
  // =============================================================================
  
  if (loading) {
    return (
      <div className="competitor-analysis-detail">
        <div className="detail-header">
          <h1>🎯 Competitor Analysis - Detailed Insights</h1>
          <p>Comprehensive market positioning and competitive landscape analysis</p>
        </div>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading competitor analysis data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="competitor-analysis-detail">
        <div className="detail-header">
          <h1>🎯 Competitor Analysis - Detailed Insights</h1>
          <p>Comprehensive market positioning and competitive landscape analysis</p>
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
      <div className="competitor-analysis-detail">
        <div className="detail-header">
          <h1>🎯 Competitor Analysis - Detailed Insights</h1>
          <p>Comprehensive market positioning and competitive landscape analysis</p>
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
  const topCompetitors = competitors?.top_competitors || [];
  
  // Extract actual competitor data from the API response
  const competitorMetrics = {
    totalCompetitors: competitors?.unique_entities || 0,
    mentionVolume: competitors?.total_entities_mentions || 0,
    marketCoverage: competitors?.extreme_networks_detection_rate || 0,
    competitionLevel: topCompetitors.length > 5 ? 'High' : topCompetitors.length > 2 ? 'Medium' : 'Low'
  };

  // =============================================================================
  // COMPONENT RENDER
  // =============================================================================
  
  return (
    <div className="competitor-analysis-detail">
      
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
                This page provides comprehensive competitive intelligence analysis by examining 
                how your brand (Extreme Networks) compares to competitors across different 
                research queries and market contexts. It tracks competitor mentions, market 
                positioning, and visibility trends to help you understand your competitive 
                landscape and identify strategic opportunities.
              </p>
            </div>
            
            <div className="guide-section">
              <h3>📈 Key Metrics Explained</h3>
              <div className="metrics-explanation">
                <div className="metric-explanation">
                  <strong>Top Competitors Surfaced:</strong> Total number of unique competitor entities identified across all your research queries.
                </div>
                <div className="metric-explanation">
                  <strong>Market Coverage:</strong> Your brand's visibility percentage compared to competitors in the same research contexts.
                </div>
                <div className="metric-explanation">
                  <strong>Competition Level:</strong> Assessment of competitive intensity based on the number of competitors identified.
                </div>
                <div className="metric-explanation">
                  <strong>Mention Volume:</strong> Total number of competitor mentions across all analyzed queries and responses.
                </div>
              </div>
            </div>
            
            <div className="guide-section">
              <h3>🏆 Competitor Insights</h3>
              <p>
                Shows detailed breakdown of competitor mentions, including:
                <br/>• <strong>Competitor Names:</strong> Specific companies and brands identified
                <br/>• <strong>Context Analysis:</strong> What types of queries and research areas competitors appear in
                <br/>• <strong>Market Positioning:</strong> Relative visibility and presence compared to your brand
              </p>
            </div>
            
            <div className="guide-section">
              <h3>🌍 Market Share of Visibility</h3>
              <p>
                Visual representation of brand visibility distribution showing:
                <br/>• <strong>Your Brand:</strong> Extreme Networks' visibility percentage
                <br/>• <strong>Top Competitors:</strong> Leading competitors' visibility percentages
                <br/>• <strong>Visibility Gap:</strong> The difference between your brand and top competitor visibility
                <br/>• <strong>Market Coverage:</strong> How comprehensively you're covering the competitive landscape
              </p>
            </div>
            
            <div className="guide-section">
              <h3>📊 Strategic Insights</h3>
              <p>
                Use this data to identify competitive opportunities, understand market positioning, 
                track competitor activity trends, and optimize your competitive intelligence 
                research strategy. The insights help you stay ahead of market changes and 
                position your brand effectively against competitors.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* =============================================================================
          DETAIL HEADER
          ============================================================================= */}
      
      <div className="detail-header">
        <h1>🎯 Competitor Analysis - Detailed Insights</h1>
        <p>Comprehensive market positioning and competitive landscape analysis</p>
        
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
        </div>
      </div>

      {/* =============================================================================
          COMPETITOR OVERVIEW
          ============================================================================= */}
      
      <div className="overview-section">
        <h2>📊 Competitor Overview</h2>
        <div className="overview-grid">
          <div className="overview-card primary">
            <div className="overview-header">
              <span className="overview-icon">🎯</span>
              <h3>Top Competitors Surfaced</h3>
            </div>
            <div className="overview-value">{competitorMetrics.totalCompetitors}</div>
            <div className="overview-trend">
              {competitorMetrics.totalCompetitors > 0 
                ? `${topCompetitors.length} entities in same results` 
                : 'No competitors detected'
              }
            </div>
          </div>
          
          <div className="overview-card">
            <div className="overview-header">
              <span className="overview-icon">📈</span>
              <h3>Total Mention Volume</h3>
            </div>
            <div className="overview-value">
              {competitorMetrics.mentionVolume}
            </div>
            <div className="overview-trend">
              {competitorMetrics.mentionVolume > 0 
                ? 'Cited in AI answers' 
                : 'No mentions found'
              }
            </div>
          </div>
        </div>
      </div>

      {/* =============================================================================
          TOP COMPETITORS SURFACED
          ============================================================================= */}
      
      <div className="competitors-section">
        <h2>🏆 Top Competitors Surfaced (Entities in Same Results)</h2>
        <div className="competitors-grid">
          {topCompetitors.length > 0 ? (
            topCompetitors.slice(0, 6).map((competitor, index) => (
              <div key={index} className="competitor-card">
                <div className="competitor-rank">#{index + 1}</div>
                <div className="competitor-header">
                  <h3>{competitor.name}</h3>
                  <span className="competitor-category">
                    {competitor.category || 'Technology'}
                  </span>
                </div>
                <div className="competitor-stats">
                  <div className="stat-item">
                    <span className="stat-label">Mentions:</span>
                    <span className="stat-value">{competitor.mentions || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Avg Position:</span>
                    <span className="stat-value">
                      {competitor.avg_rank && competitor.avg_rank !== "N/A" 
                        ? `#${competitor.avg_rank}` 
                        : 'N/A'
                      }
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Visibility:</span>
                    <span className="stat-value">
                      {competitor.mentions > 0 && competitorMetrics.mentionVolume > 0
                        ? `${((competitor.mentions / competitorMetrics.mentionVolume) * 100).toFixed(1)}%`
                        : 'N/A'
                      }
                    </span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="no-data-message">
              <p>No competitor entities detected in automated query results</p>
            </div>
          )}
        </div>
      </div>

      {/* =============================================================================
          MENTION VOLUME ANALYSIS
          ============================================================================= */}
      
      <div className="mention-analysis-section">
        <h2>📈 Mention Volume Analysis (AI Answer Citations)</h2>
        <div className="mention-analysis-grid">
          <div className="mention-chart-card">
            <h3>Mention Distribution by Competitor</h3>
            <div className="mention-chart">
              {topCompetitors.length > 0 ? (
                topCompetitors.slice(0, 5).map((competitor, index) => (
                  <div key={index} className="mention-bar-item">
                    <span className="competitor-name">{competitor.name}</span>
                    <div className="mention-bar-container">
                      <div 
                        className="mention-bar" 
                        style={{
                          width: `${(competitor.mentions / competitorMetrics.mentionVolume * 100) || 0}%`
                        }}
                      ></div>
                    </div>
                    <span className="mention-count">{competitor.mentions || 0}</span>
                  </div>
                ))
              ) : (
                <div className="no-data-message">
                  <p>No mention volume data available</p>
                </div>
              )}
            </div>
          </div>
          
          <div className="mention-insights-card">
            <h3>Key Insights</h3>
            <div className="insights-list">
              {topCompetitors.length > 0 ? (
                <>
                  <div className="insight-item">
                    <span className="insight-icon">🔥</span>
                    <div className="insight-content">
                      <h4>Most Mentioned</h4>
                      <p>{topCompetitors[0]?.name || 'N/A'} leads with {topCompetitors[0]?.mentions || 0} citations</p>
                    </div>
                  </div>
                  <div className="insight-item">
                    <span className="insight-icon">📊</span>
                    <div className="insight-content">
                      <h4>Total Volume</h4>
                      <p>{competitorMetrics.mentionVolume} total competitor mentions across all queries</p>
                    </div>
                  </div>
                  <div className="insight-item">
                    <span className="insight-icon">🎯</span>
                    <div className="insight-content">
                      <h4>Coverage</h4>
                      <p>Measures how comprehensively your competitive intelligence queries are covering the market landscape and identifying key competitors across different research contexts and query types.</p>
                    </div>
                  </div>
                </>
              ) : (
                <div className="no-data-message">
                  <p>No insights available without competitor data</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>



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

export default CompetitorAnalysisDetail;