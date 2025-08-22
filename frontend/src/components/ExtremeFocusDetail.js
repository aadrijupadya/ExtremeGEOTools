import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getExtremeFocusMetrics } from '../services/api';
import './ExtremeFocusDetail.css';

// Function to convert markdown to HTML
const markdownToHtml = (text) => {
  if (!text) return '';
  
  return text
    // Bold text: **text** -> <strong>text</strong>
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Italic text: *text* -> <em>text</em>
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Code: `text` -> <code>text</code>
    .replace(/`(.*?)`/g, '<code>$1</code>')
    // Line breaks: \n -> <br>
    .replace(/\n/g, '<br>');
};

const ExtremeFocusDetail = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedGap, setSelectedGap] = useState(null);
  const [showGapModal, setShowGapModal] = useState(false);
  const [selectedContext, setSelectedContext] = useState(null);
  const [showContextModal, setShowContextModal] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Get filters from URL params with defaults
  const engine = searchParams.get('engine') || 'all';
  const days = parseInt(searchParams.get('days') || '30');
  
  // Calculate date range - fix the date calculation
  const today = new Date();
  const endDate = today.toISOString().split('T')[0];
  const startDate = new Date(today.getTime() - days * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

  useEffect(() => {
    fetchExtremeFocusData();
  }, [engine, days]);

  const fetchExtremeFocusData = async () => {
    setLoading(true);
    setError(null);
    try {
      const engineParam = engine === 'all' ? null : engine;
      const response = await getExtremeFocusMetrics(startDate, endDate, engineParam);
      setData(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newEngine, newDays) => {
    const params = new URLSearchParams(searchParams);
    if (newEngine !== 'all') {
      params.set('engine', newEngine);
    } else {
      params.delete('engine');
    }
    params.set('days', newDays.toString());
    setSearchParams(params);
  };

  if (loading) {
    return (
      <div className="extreme-focus-detail">
        <div className="loading">Loading Extreme Focus metrics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="extreme-focus-detail">
        <div className="error">Error: {error}</div>
        <button onClick={fetchExtremeFocusData} className="retry-btn">Retry</button>
      </div>
    );
  }

  if (!data || !data.metrics) {
    // Add some debugging info
    console.log('ExtremeFocusDetail - No data or metrics:', { data, hasData: !!data, hasMetrics: !!(data && data.metrics) });
    
    return (
      <div className="extreme-focus-detail">
        <div className="detail-header">
          <h1>Extreme Focus - AI Search Visibility Analysis</h1>
          <p className="subtitle">
            Comprehensive analysis of how Extreme Networks appears in AI-generated responses
          </p>
        </div>

        <div className="info-guide">
          <details open>
            <summary>What This Page Shows</summary>
            <div className="guide-content">
              <p><strong>AI Search Visibility:</strong> How often Extreme Networks is mentioned in neutral queries (excluding branded queries like "Cisco vs Juniper"), along with citation and domain metrics from runs where Extreme was mentioned.</p>
              <p><strong>Query Coverage Gaps:</strong> Identifies neutral queries where Extreme should be showing up but is missing from AI responses. Click on any gap to see the full query and AI response.</p>
              <p><strong>Brand Intent Analysis:</strong> Categorizes queries where Extreme was mentioned by intent type (comparison, product-specific, review, etc.) with clickable examples to view full responses.</p>
              <p><strong>Entity Associations:</strong> Shows what products and keywords AI associates with Extreme (Wi-Fi 6E, SASE, campus networking, etc.).</p>
              <p><strong>Interactive Features:</strong> Click on coverage gaps and context examples to view complete AI responses in detailed modals with proper markdown formatting.</p>
            </div>
          </details>
        </div>

        <div className="filter-controls">
          <div className="filter-group">
            <label>Engine:</label>
            <select 
              value={engine} 
              onChange={(e) => handleFilterChange(e.target.value, days)}
              className="filter-select"
            >
              <option value="all">All Engines</option>
              <option value="openai">OpenAI</option>
              <option value="perplexity">Perplexity</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label>Time Period:</label>
            <select 
              value={days} 
              onChange={(e) => handleFilterChange(engine, parseInt(e.target.value))}
              className="filter-select"
            >
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="60">Last 60 days</option>
              <option value="90">Last 90 days</option>
            </select>
          </div>
        </div>

        <div className="no-data">
          <h2>No Data Available</h2>
          <p>No automated runs found for the selected criteria:</p>
          <ul>
            <li><strong>Time Period:</strong> {startDate} to {endDate}</li>
            <li><strong>Engine:</strong> {engine === 'all' ? 'All Engines' : engine}</li>
          </ul>
          <p>This could mean:</p>
          <ul>
            <li>No automated queries have been run yet</li>
            <li>The selected time period doesn't have data</li>
            <li>The selected engine doesn't have runs</li>
          </ul>
          <p>Try adjusting the filters or check if automated queries are running.</p>
        </div>
      </div>
    );
  }

  const { metrics } = data;

  // Add debugging info
  console.log('ExtremeFocusDetail - Data structure:', { 
    data, 
    metrics, 
    coverageGaps: metrics?.coverage_gaps,
    answerPositioning: metrics?.answer_positioning,
    entityAssociations: metrics?.entity_associations,
    trends: metrics?.trends
  });

  return (
    <div className="extreme-focus-detail">
      {/* Header */}
      <div className="detail-header">
        <h1>Extreme Focus - AI Search Visibility Analysis</h1>
        <p className="subtitle">
          Comprehensive analysis of how Extreme Networks appears in AI-generated responses
        </p>
      </div>

      {/* Info Guide */}
      <div className="info-guide">
        <details>
          <summary>What This Page Shows</summary>
          <div className="guide-content">
            <p><strong>AI Search Visibility:</strong> How often Extreme Networks is mentioned in neutral queries (excluding branded queries like "Cisco vs Juniper"), along with citation and domain metrics from runs where Extreme was mentioned.</p>
            <p><strong>Query Coverage Gaps:</strong> Identifies neutral queries where Extreme should be showing up but is missing from AI responses. Click on any gap to see the full query and AI response.</p>
            <p><strong>Brand Intent Analysis:</strong> Categorizes queries where Extreme was mentioned by intent type (comparison, product-specific, review, etc.) with clickable examples to view full responses.</p>
            <p><strong>Entity Associations:</strong> Shows what products and keywords AI associates with Extreme (Wi-Fi 6E, SASE, campus networking, etc.).</p>
            <p><strong>Interactive Features:</strong> Click on coverage gaps and context examples to view complete AI responses in detailed modals with proper markdown formatting.</p>
          </div>
        </details>
      </div>

      {/* Filters */}
      <div className="filter-controls">
        <div className="filter-group">
          <label>Engine:</label>
          <select 
            value={engine} 
            onChange={(e) => handleFilterChange(e.target.value, days)}
            className="filter-select"
          >
            <option value="all">All Engines</option>
            <option value="openai">OpenAI</option>
            <option value="perplexity">Perplexity</option>
          </select>
        </div>
        
        <div className="filter-group">
          <label>Time Period:</label>
          <select 
            value={days} 
            onChange={(e) => handleFilterChange(engine, parseInt(e.target.value))}
            className="filter-select"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="60">Last 60 days</option>
            <option value="90">Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="summary-stats">
        <div className="stat-card">
          <h3>AI Search Visibility</h3>
          <div className="stat-value">{metrics.ai_search_visibility?.total_mentions || 0}</div>
          <div className="stat-label">Total Mentions</div>
          <div className="stat-secondary">
            {metrics.ai_search_visibility?.mention_rate_pct || 0}% mention rate
          </div>
          <div className="stat-note">
            From {metrics.ai_search_visibility?.neutral_queries_analyzed || 0} neutral queries
          </div>
        </div>
        
        <div className="stat-card">
          <h3>Coverage Gaps</h3>
          <div className="stat-value">{metrics.coverage_gaps?.total_gaps || 0}</div>
          <div className="stat-label">Missed Opportunities</div>
          <div className="stat-secondary">
            {metrics.coverage_gaps?.overall_gap_rate_pct || 0}% gap rate
          </div>
        </div>
        
        <div className="stat-card">
          <h3>Citations & Domains</h3>
          <div className="stat-value">{metrics.ai_search_visibility?.total_citations || 0}</div>
          <div className="stat-label">Extreme-Related Citations</div>
          <div className="stat-secondary">
            {metrics.ai_search_visibility?.total_domains || 0} unique domains
          </div>
          <div className="stat-note">
            Only from runs where Extreme was mentioned
          </div>
        </div>
      </div>

      {/* Coverage Gaps Analysis */}
      <div className="metrics-section">
        <h2>Query Coverage Gaps</h2>
        <p>Identifies where Extreme should be mentioned but is missing from AI responses.</p>
        
        {/* Gap Summary */}
        <div className="gap-summary">
          <div className="gap-summary-stats">
            <div className="gap-summary-item">
              <strong>Total Gaps:</strong> {metrics.coverage_gaps?.total_gaps || 0}
            </div>
            <div className="gap-summary-item">
              <strong>Overall Gap Rate:</strong> {metrics.coverage_gaps?.overall_gap_rate_pct || 0}%
            </div>
            <div className="gap-summary-item">
              <strong>Queries Analyzed:</strong> {metrics.coverage_gaps?.total_queries_analyzed || 0}
            </div>
            <div className="gap-summary-item">
              <strong>Branded Queries Filtered:</strong> {metrics.coverage_gaps?.branded_queries_filtered || 0}
            </div>
            <div className="gap-summary-item">
              <strong>Analysis:</strong> {metrics.coverage_gaps?.total_gaps > 0 ? 
                `${metrics.coverage_gaps.total_gaps} neutral queries where Extreme should appear but doesn't` : 
                'No coverage gaps detected in neutral queries'
              }
            </div>
          </div>
          <div className="gap-summary-note">
            <p><strong>Note:</strong> Only neutral queries (e.g., "top enterprise Wi-Fi solutions") are analyzed for gaps. 
            Branded queries (e.g., "Cisco Wi-Fi 7 strengths") are excluded since they're focused on specific competitors.</p>
          </div>
        </div>
        
        {/* All Gaps Detailed View */}
        {metrics.coverage_gaps?.all_gaps && Array.isArray(metrics.coverage_gaps.all_gaps) && metrics.coverage_gaps.all_gaps.length > 0 && (
          <div className="all-gaps-view">
            <h3>All Coverage Gaps ({metrics.coverage_gaps.all_gaps.length})</h3>
            <p>Detailed view of all queries where Extreme should have been mentioned but wasn't. <strong>Scroll to see more gaps.</strong></p>
            <p className="gaps-instruction"><strong>Click on any gap to read full response</strong></p>
            
            <div className="gaps-table">
              {metrics.coverage_gaps.all_gaps.map((gap, idx) => (
                <div 
                  key={idx} 
                  className="gap-row clickable"
                  onClick={() => {
                    setSelectedGap(gap);
                    setShowGapModal(true);
                  }}
                >
                  <div className="gap-main">
                    <div className="gap-query-full">{gap.query}</div>
                    <div className="gap-meta">
                      <span className="gap-engine">{gap.engine}</span>
                      <span className="gap-category">{gap.why_extreme_should_appear}</span>
                    </div>
                  </div>
                  <div className="gap-competitors-full">
                    <strong>Competitors:</strong> {Array.isArray(gap.competitors_mentioned) && gap.competitors_mentioned.length > 0 ? gap.competitors_mentioned.join(', ') : 'None detected'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Brand Intent Analysis */}
      <div className="metrics-section">
        <h2>Brand Intent Analysis</h2>
        <p>Intent split of queries where Extreme Networks was mentioned.</p>
        
        <div className="intent-breakdown">
          {Object.entries(metrics.answer_positioning?.intent_breakdown || {}).map(([intent, count]) => (
            <div key={intent} className="intent-item">
              <div className="intent-name">{intent.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>
              <div className="intent-count">{count}</div>
              <div className="intent-bar">
                <div 
                  className="intent-fill" 
                  style={{width: `${(count / (metrics.answer_positioning?.total_extreme_mentions || 1)) * 100}%`}}
                ></div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Context Examples by Intent Type */}
        <div className="context-examples">
          <h3>Context Examples by Intent Type</h3>
          <div className="context-examples-container">
            {Object.entries(metrics.answer_positioning?.context_examples || {}).map(([intent, examples]) => (
              examples.length > 0 && (
                <div key={intent} className="intent-examples">
                  <h4>{intent.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Examples</h4>
                  {examples.map((example, idx) => (
                    <div 
                      key={idx} 
                      className="context-example clickable"
                      onClick={() => {
                        setSelectedContext(example);
                        setShowContextModal(true);
                      }}
                    >
                      <div className="context-query">
                        <strong>Query:</strong> {example?.query || 'No query text'}
                      </div>
                      <div className="context-answer">
                        <strong>Answer Preview:</strong> 
                        <span 
                          dangerouslySetInnerHTML={{ 
                            __html: markdownToHtml(example?.answer_preview || 'No answer text') 
                          }}
                        />
                      </div>
                      <div className="context-engine">
                        <strong>Engine:</strong> {example?.engine || 'Unknown'}
                      </div>
                    </div>
                  ))}
                </div>
              )
            ))}
          </div>
        </div>
      </div>

      {/* Entity Associations */}
      <div className="metrics-section">
        <h2>Entity Associations</h2>
        <p>What products and keywords AI associates with Extreme Networks.</p>
        
        <div className="associations-grid">
          <div className="association-group">
            <h3>Product Associations</h3>
            {Object.entries(metrics.entity_associations?.product_associations || {}).map(([product, count]) => (
              <div key={product} className="association-item">
                <span className="association-name">{product}</span>
                <span className="association-count">{count}</span>
              </div>
            ))}
          </div>
          
          <div className="association-group">
            <h3>Keyword Associations</h3>
            {Object.entries(metrics.entity_associations?.keyword_associations || {}).map(([keyword, count]) => (
              <div key={keyword} className="association-item">
                <span className="association-name">{keyword}</span>
                <span className="association-count">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Gap Detail Modal */}
      {showGapModal && selectedGap && (
        <div className="gap-modal-overlay" onClick={() => setShowGapModal(false)}>
          <div className="gap-modal" onClick={(e) => e.stopPropagation()}>
            <div className="gap-modal-header">
              <h2>Coverage Gap Details</h2>
              <button 
                className="gap-modal-close"
                onClick={() => setShowGapModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="gap-modal-content">
              <div className="gap-modal-section">
                <h3>Query</h3>
                <p 
                  className="gap-modal-query" 
                  dangerouslySetInnerHTML={{ __html: markdownToHtml(selectedGap.full_query || selectedGap.query) }}
                />
              </div>
              
              <div className="gap-modal-section">
                <h3>Why Extreme Should Appear</h3>
                <p 
                  className="gap-modal-category" 
                  dangerouslySetInnerHTML={{ __html: markdownToHtml(selectedGap.why_extreme_should_appear) }}
                />
              </div>
              
              <div className="gap-modal-section">
                <h3>Engine Used</h3>
                <p className="gap-modal-engine">{selectedGap.engine}</p>
              </div>
              
              <div className="gap-modal-section">
                <h3>Competitors Mentioned</h3>
                <p 
                  className="gap-modal-competitors"
                  dangerouslySetInnerHTML={{ 
                    __html: markdownToHtml(
                      Array.isArray(selectedGap.competitors_mentioned) && selectedGap.competitors_mentioned.length > 0 
                        ? selectedGap.competitors_mentioned.join(', ') 
                        : 'None detected'
                    )
                  }}
                />
              </div>
              
              <div className="gap-modal-section">
                <h3>Full AI Response</h3>
                <div 
                  className="gap-modal-response"
                  dangerouslySetInnerHTML={{ 
                    __html: markdownToHtml(selectedGap.full_ai_response || selectedGap.ai_response_preview || 'No response text available') 
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Context Example Modal */}
      {showContextModal && selectedContext && (
        <div className="context-example-modal-overlay" onClick={() => setShowContextModal(false)}>
          <div className="context-example-modal" onClick={(e) => e.stopPropagation()}>
            <div className="context-example-modal-header">
              <h2>Context Example Details</h2>
              <button 
                className="context-example-modal-close"
                onClick={() => setShowContextModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="context-example-modal-content">
              <div className="context-example-modal-section">
                <h3>Query</h3>
                <p 
                  className="context-example-modal-query" 
                  dangerouslySetInnerHTML={{ __html: markdownToHtml(selectedContext.query) }}
                />
              </div>
              
              <div className="context-example-modal-section">
                <h3>Full Answer</h3>
                <div 
                  className="context-example-modal-answer"
                  dangerouslySetInnerHTML={{ 
                    __html: markdownToHtml(selectedContext.full_answer || selectedContext.answer_preview || 'No answer text available') 
                  }}
                />
              </div>
              
              <div className="context-example-modal-section">
                <h3>Engine</h3>
                <p className="context-example-modal-engine">{selectedContext.engine}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExtremeFocusDetail;
