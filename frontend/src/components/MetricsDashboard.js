import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import AutomatedQueryDashboard from './AutomatedQueryDashboard';
import './MetricsDashboard.css';

const MetricsDashboard = () => {
  const [metrics, setMetrics] = useState([]);
  const [summary, setSummary] = useState({});
  const [entities, setEntities] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [dateRange, setDateRange] = useState({
    start: format(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
    end: format(new Date(), 'yyyy-MM-dd')
  });
  const [selectedEngine, setSelectedEngine] = useState('');

  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    // Check backend connection first
    checkConnection();
    
    // Add a small delay to ensure the component is fully mounted
    const timer = setTimeout(() => {
      if (isConnected) {
        fetchMetrics();
        fetchSummary();
        fetchEntities();
      }
    }, 100);
    
    return () => clearTimeout(timer);
  }, [dateRange, selectedEngine, isConnected]);

  const checkConnection = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      const data = await response.json();
      setIsConnected(!!data.ok);
    } catch (error) {
      console.error('Backend not connected:', error);
      setIsConnected(false);
    }
  };

  const fetchMetrics = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        start_date: dateRange.start,
        end_date: dateRange.end
      });
      if (selectedEngine) params.append('engine', selectedEngine);
      
      const response = await fetch(`${API_BASE}/metrics/daily?${params}`);
      const data = await response.json();
      setMetrics(data.metrics || []);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await fetch(`${API_BASE}/metrics/summary?days=30`);
      const data = await response.json();
      console.log('Summary data received:', data);
      setSummary(data);
    } catch (error) {
      console.error('Failed to fetch summary:', error);
    }
  };

  const fetchEntities = async () => {
    try {
      const params = new URLSearchParams({ days: '30' });
      if (selectedEngine) params.append('engine', selectedEngine);
      
      const response = await fetch(`${API_BASE}/metrics/entities?${params}`);
      const data = await response.json();
      setEntities(data.entities || {});
    } catch (error) {
      console.error('Failed to fetch entities:', error);
    }
  };

  const computeMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE}/metrics/compute?target_date=${dateRange.end}`, {
        method: 'POST'
      });
      const data = await response.json();
      alert(`Metrics computed: ${data.message}`);
      fetchMetrics(); // Refresh data
    } catch (error) {
      console.error('Failed to compute metrics:', error);
      alert('Failed to compute metrics');
    }
  };

  const renderMetricsTable = () => {
    if (metrics.length === 0) {
      return <div className="no-data">No metrics available for the selected date range</div>;
    }

    return (
      <div className="metrics-table">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Engine</th>
              <th>Context</th>
              <th>Runs</th>
              <th>Cost ($)</th>
              <th>Citations</th>
              <th>Domains</th>
              <th>Brand Mentions</th>
              <th>Share of Voice (%)</th>
              <th>Visibility Score</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((metric, index) => (
              <tr key={index}>
                <td>{metric.date}</td>
                <td>{metric.engine}</td>
                <td>{metric.brand_context}</td>
                <td>{metric.total_runs}</td>
                <td>${Number(metric.total_cost_usd || 0).toFixed(4)}</td>
                <td>{metric.total_citations}</td>
                <td>{metric.unique_domains}</td>
                <td>{metric.brand_mentions}</td>
                <td>{Number(metric.share_of_voice_pct || 0).toFixed(1)}%</td>
                <td>{Number(metric.avg_visibility_score || 0).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderSummaryCards = () => {
    if (!summary || !summary.period_days) return null;

    return (
      <div className="summary-cards">
        <div className="summary-card">
          <h3>Total Runs</h3>
          <div className="card-value">{summary.total_runs || 0}</div>
        </div>
        <div className="summary-card">
          <h3>Total Cost</h3>
          <div className="card-value">${(summary.total_cost_usd || 0).toFixed(4)}</div>
        </div>
        <div className="summary-card">
          <h3>Total Citations</h3>
          <div className="card-value">{summary.total_citations || 0}</div>
        </div>
        <div className="summary-card">
          <h3>Avg Visibility</h3>
          <div className="card-value">{Number(summary.avg_visibility_score || 0).toFixed(2)}</div>
        </div>
        <div className="summary-card">
          <h3>Brand Share</h3>
          <div className="card-value">{Number(summary.brand_share_of_voice || 0).toFixed(1)}%</div>
        </div>
      </div>
    );
  };

  const renderEntityMetrics = () => {
    if (!entities.extreme_networks && !entities.competitors) return null;

    return (
      <div className="entity-metrics">
        <h3>Entity Visibility</h3>
        <div className="entity-cards">
          {entities.extreme_networks && (
            <div className="entity-card brand">
              <h4>Extreme Networks</h4>
              <div className="entity-stats">
                <div>Total Mentions: {entities.extreme_networks.total_mentions}</div>
                <div>Avg Share of Voice: {entities.extreme_networks.avg_share_of_voice}%</div>
              </div>
            </div>
          )}
          {entities.competitors && (
            <div className="entity-card competitor">
              <h4>Competitors</h4>
              <div className="entity-stats">
                <div>Total Mentions: {entities.competitors.total_mentions}</div>
                <div>Avg Share of Voice: {entities.competitors.avg_share_of_voice}%</div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="metrics-dashboard">
      <div className="dashboard-header">
        <h1>Metrics Dashboard</h1>
        <div className="connection-status">
          <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
          {isConnected ? 'Backend Connected' : 'Backend Disconnected'}
        </div>
        <div className="controls">
          <div className="date-controls">
            <label>
              Start Date:
              <input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
              />
            </label>
            <label>
              End Date:
              <input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
              />
            </label>
          </div>
          <div className="filter-controls">
            <label>
              Engine:
              <select value={selectedEngine} onChange={(e) => setSelectedEngine(e.target.value)}>
                <option value="">All Engines</option>
                <option value="openai">OpenAI</option>
                <option value="perplexity">Perplexity</option>
              </select>
            </label>
          </div>
          <button onClick={computeMetrics} className="compute-btn">
            Compute Metrics
          </button>
        </div>
      </div>

      <div className="dashboard-content">
        {!isConnected ? (
          <div className="dashboard-section">
            <div className="no-connection">
              <h2>Backend Not Connected</h2>
              <p>Please start the backend server to view metrics data.</p>
              <button onClick={checkConnection} className="retry-btn">
                Retry Connection
              </button>
            </div>
          </div>
        ) : (
          <>
            {renderSummaryCards()}
            
            <div className="dashboard-section">
              <h2>Daily Metrics</h2>
              {isLoading ? <div className="loading">Loading metrics...</div> : renderMetricsTable()}
            </div>

            <div className="dashboard-section">
              {renderEntityMetrics()}
            </div>

            {/* Automated Query Results Section */}
            <div className="dashboard-section automated-section">
              <h2>🤖 Automated Query Results</h2>
              <p className="section-description">
                Focused analysis of automated query results, competitor mentions, and Extreme Networks visibility.
              </p>
              <AutomatedQueryDashboard />
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default MetricsDashboard;
