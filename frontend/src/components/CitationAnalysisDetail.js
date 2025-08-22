import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getCitationAnalysis } from '../services/api';
import './CitationAnalysisDetail.css';

const CitationAnalysisDetail = () => {
  const [searchParams] = useSearchParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSource, setSelectedSource] = useState(null);
  const [showSourceModal, setShowSourceModal] = useState(false);

  // Function to categorize domains
  const categorizeDomain = (domain) => {
    const domainLower = domain.toLowerCase();
    
    // Branded/Vendor websites (any company's own domain)
    if (domainLower.includes('extremenetworks') || domainLower.includes('extreme') ||
        domainLower.includes('cisco') || domainLower.includes('meraki') ||
        domainLower.includes('juniper') || domainLower.includes('mist') ||
        domainLower.includes('aruba') || domainLower.includes('hpe') ||
        domainLower.includes('fortinet') || domainLower.includes('fortigate') ||
        domainLower.includes('paloalto') || domainLower.includes('checkpoint') ||
        domainLower.includes('ubiquiti') || domainLower.includes('ruckus') ||
        domainLower.includes('netgear') || domainLower.includes('linksys') ||
        domainLower.includes('zyxel') || domainLower.includes('dlink')) {
      return { category: 'Branded', color: '#6366f1' };
    }
    
    // Review & Rating platforms
    if (domainLower.includes('peerspot') || domainLower.includes('g2') || 
        domainLower.includes('trustradius') || domainLower.includes('capterra') ||
        domainLower.includes('reviews') || domainLower.includes('rating')) {
      return { category: 'Reviews', color: '#8b5cf6' };
    }
    
    // Research & Analysis firms
    if (domainLower.includes('gartner') || domainLower.includes('idc') || 
        domainLower.includes('marketsandmarkets') || domainLower.includes('grandview') ||
        domainLower.includes('fortunebusiness') || domainLower.includes('forrester') ||
        domainLower.includes('analyst') || domainLower.includes('research')) {
      return { category: 'Research', color: '#f97316' };
    }
    
    // Tech Media & News
    if (domainLower.includes('techtarget') || domainLower.includes('networkworld') || 
        domainLower.includes('crn') || domainLower.includes('sdxcentral') ||
        domainLower.includes('techradar') || domainLower.includes('itpro') ||
        domainLower.includes('venturebeat') || domainLower.includes('techcrunch') ||
        domainLower.includes('zdnet') || domainLower.includes('computerworld')) {
      return { category: 'Tech Media', color: '#10b981' };
    }
    
    // Reference & Educational
    if (domainLower.includes('wikipedia') || domainLower.includes('techopedia') ||
        domainLower.includes('stackoverflow') || domainLower.includes('reddit') ||
        domainLower.includes('.edu') || domainLower.includes('tutorial')) {
      return { category: 'Reference', color: '#64748b' };
    }
    
    // Career & Corporate info
    if (domainLower.includes('glassdoor') || domainLower.includes('linkedin') ||
        domainLower.includes('comparably') || domainLower.includes('indeed') ||
        domainLower.includes('career') || domainLower.includes('jobs')) {
      return { category: 'Career', color: '#ec4899' };
    }
    
    // Investor Relations & Financial
    if (domainLower.includes('investor') || domainLower.includes('gcs-web') ||
        domainLower.includes('sec.gov') || domainLower.includes('finance') ||
        domainLower.includes('earnings') || domainLower.includes('ir.')) {
      return { category: 'Financial', color: '#6b7280' };
    }
    
    // System Integrators & Partners
    if (domainLower.includes('nomios') || domainLower.includes('cloudtango') ||
        domainLower.includes('syntrix') || domainLower.includes('fuse.systems') ||
        domainLower.includes('integrator') || domainLower.includes('partner')) {
      return { category: 'Partners', color: '#14b8a6' };
    }
    
    // Default - Neutral/Other
    return { category: 'Neutral', color: '#9ca3af' };
  };

  const engine = searchParams.get('engine') || 'all';
  const days = parseInt(searchParams.get('days') || '7');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const today = new Date();
        const startDate = new Date(today.getTime() - days * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        const endDate = today.toISOString().split('T')[0];
        
        const response = await getCitationAnalysis(startDate, endDate, engine === 'all' ? null : engine);
        setData(response);
      } catch (err) {
        setError(err.message);
        console.error('Error fetching citation analysis:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [engine, days]);

  if (loading) {
    return (
      <div className="citation-analysis-page">
        <div className="loading">Loading citation analysis...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="citation-analysis-page">
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  if (!data || data.total_runs_analyzed === 0) {
    return (
      <div className="citation-analysis-page">
        <div className="no-data">
          <h1>Citation Analysis</h1>
          <p>No citation data found for the selected criteria.</p>
          <p>This could mean:</p>
          <ul>
            <li>No runs were found in the selected date range</li>
            <li>No runs mentioned Extreme Networks</li>
            <li>No citations/URLs were found in the responses</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="citation-analysis-page">
      {/* Header */}
      <div className="page-header">
        <h1>Citation Analysis</h1>
        <p>Most cited sources about/from Extreme Networks in AI responses</p>
      </div>

      {/* Info Guide */}
      <div className="info-guide">
        <details>
          <summary>What This Page Shows</summary>
          <div className="info-content">
            <p><strong>Citation Sources:</strong> Domains and websites that are most frequently cited when AI mentions Extreme Networks, showing which sources are considered authoritative.</p>
            <p><strong>Source Breakdown:</strong> Detailed analysis of each citation source including citation count, URLs, and how often they appear across different AI responses.</p>
            <p><strong>Citation Quality:</strong> Understanding which sources AI relies on most when discussing Extreme Networks, helping identify key reference materials.</p>
            <p><strong>Interactive Features:</strong> Click on any citation source to see all URLs and detailed breakdown of how it's referenced across different queries.</p>
          </div>
        </details>
      </div>

      {/* Filter Controls */}
      <div className="filter-controls">
        <div className="filter-group">
          <label>Time Period:</label>
          <select 
            value={days} 
            onChange={(e) => {
              const newDays = parseInt(e.target.value);
              searchParams.set('days', newDays.toString());
              window.location.search = searchParams.toString();
            }}
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
          </select>
        </div>
        
        <div className="filter-group">
          <label>Engine:</label>
          <select 
            value={engine} 
            onChange={(e) => {
              const newEngine = e.target.value;
              searchParams.set('engine', newEngine);
              window.location.search = searchParams.toString();
            }}
          >
            <option value="all">All Engines</option>
            <option value="openai">OpenAI</option>
            <option value="perplexity">Perplexity</option>
          </select>
        </div>
      </div>

      {/* Engine Status */}
      <div className="engine-status">
        <strong>You are now seeing results for:</strong>
        <div className="engine-display">
          {engine === 'all' ? (
            <span>All Engines</span>
          ) : (
            <span className="engine-name">
              {engine === 'openai' ? 'OpenAI' : 'Perplexity'}
            </span>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="summary-stats">
        <div className="stat-card">
          <h3>Total Citations</h3>
          <div className="stat-value">{data.citation_analysis?.summary?.total_citations || 0}</div>
          <div className="stat-label">URLs Referenced</div>
          <div className="stat-secondary">
            Across {data.total_runs_analyzed || 0} AI responses
          </div>
        </div>
        
        <div className="stat-card">
          <h3>Unique Sources</h3>
          <div className="stat-value">{data.citation_analysis?.domain_analysis?.total_unique_domains || 0}</div>
          <div className="stat-label">Different Domains</div>
          <div className="stat-secondary">
            Referenced in responses
          </div>
        </div>
        
        <div className="stat-card">
          <h3>Analysis Coverage</h3>
          <div className="stat-value">{data.total_runs_analyzed || 0}</div>
          <div className="stat-label">Runs Analyzed</div>
          <div className="stat-secondary">
            Where Extreme was mentioned
          </div>
        </div>
      </div>

      {/* Top Citation Sources */}
      <div className="metrics-section">
        <h2>Top Citation Sources</h2>
        <p>Most frequently cited domains across all AI responses</p>
        
        <div className="sources-table-container">
          <div className="sources-table">
            <div className="sources-header">
              <div className="source-domain">Domain</div>
              <div className="source-category">Category</div>
              <div className="source-citations">Citations</div>
              <div className="source-actions">Actions</div>
            </div>
            
            <div className="sources-list">
              {data.citation_analysis?.most_cited_sources?.top_sources?.map((source, index) => {
                const categoryInfo = categorizeDomain(source.domain);
                return (
                  <div key={index} className="source-row">
                    <div className="source-domain">
                      <strong>{source.domain}</strong>
                    </div>
                    <div className="source-category">
                      <span 
                        className="category-tag" 
                        style={{ backgroundColor: categoryInfo.color }}
                      >
                        {categoryInfo.category}
                      </span>
                    </div>
                    <div className="source-citations">
                      {source.citation_count}
                    </div>
                    <div className="source-actions">
                      <button 
                        className="view-details-btn"
                        onClick={() => {
                          setSelectedSource(source);
                          setShowSourceModal(true);
                        }}
                      >
                        View Details
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          
          <div className="sources-instruction">
            <p>Scroll to see more sources • Click on any source to view details</p>
          </div>
        </div>
      </div>

      {/* Extreme-Related Sources */}
      <div className="metrics-section">
        <h2>Extreme-Related Sources</h2>
        <p>Most frequently cited domains when AI mentions Extreme Networks</p>
        
        <div className="sources-table-container">
          <div className="sources-table">
            <div className="sources-header">
              <div className="source-domain">Domain</div>
              <div className="source-category">Category</div>
              <div className="source-citations">Citations</div>
              <div className="source-actions">Actions</div>
            </div>
            
            <div className="sources-list">
              {data.citation_analysis?.extreme_related_sources?.top_extreme_sources?.map((source, index) => {
                const categoryInfo = categorizeDomain(source.domain);
                return (
                  <div key={index} className="source-row">
                    <div className="source-domain">
                      <strong>{source.domain}</strong>
                    </div>
                    <div className="source-category">
                      <span 
                        className="category-tag" 
                        style={{ backgroundColor: categoryInfo.color }}
                      >
                        {categoryInfo.category}
                      </span>
                    </div>
                    <div className="source-citations">
                      {source.citation_count}
                    </div>
                    <div className="source-actions">
                      <button 
                        className="view-details-btn"
                        onClick={() => {
                          setSelectedSource(source);
                          setShowSourceModal(true);
                        }}
                      >
                        View Details
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          
          <div className="sources-instruction">
            <p>Scroll to see more Extreme-related sources • Click on any source to view details</p>
          </div>
        </div>
        
        <div className="analysis-note">
          <p><strong>Analysis:</strong> {data.citation_analysis?.extreme_related_sources?.total_extreme_citations || 0} citations found in {Math.round((data.citation_analysis?.summary?.extreme_mention_rate || 0) * 100)}% of runs where Extreme was mentioned.</p>
        </div>
      </div>

      {/* Source Detail Modal */}
      {showSourceModal && selectedSource && (
        <div className="source-modal-overlay" onClick={() => setShowSourceModal(false)}>
          <div className="source-modal" onClick={(e) => e.stopPropagation()}>
            <div className="source-modal-header">
              <h3>Citation Source Details: {selectedSource.domain}</h3>
              <button 
                className="source-modal-close"
                onClick={() => setShowSourceModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="source-modal-content">
              <div className="source-modal-section">
                <h4>Source Statistics</h4>
                <div className="source-stats-grid">
                  <div className="source-stat">
                    <strong>Total Citations:</strong> {selectedSource.citation_count}
                  </div>
                  <div className="source-stat">
                    <strong>Domain:</strong> {selectedSource.domain}
                  </div>
                  <div className="source-stat">
                    <strong>Unique Queries:</strong> {selectedSource.queries?.length || 0}
                  </div>
                  <div className="source-stat">
                    <strong>Runs Mentioned:</strong> {selectedSource.runs_count || 0}
                  </div>
                </div>
              </div>
              
              {selectedSource.queries && selectedSource.queries.length > 0 && (
                <div className="source-modal-section">
                  <h4>Queries Where This Source Was Cited</h4>
                  <div className="source-queries">
                    {selectedSource.queries.map((query, idx) => (
                      <div key={idx} className="source-query">
                        <span className="query-text">"{query}"</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {selectedSource.urls && selectedSource.urls.length > 0 && (
                <div className="source-modal-section">
                  <h4>Specific URLs Cited</h4>
                  <div className="source-urls">
                    {selectedSource.urls.map((url, idx) => (
                      <div key={idx} className="source-url">
                        <a href={url} target="_blank" rel="noopener noreferrer">
                          {url}
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CitationAnalysisDetail;
