import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getEnhancedAnalysis, API_BASE_URL } from '../services/api';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import './MetricsDashboard.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

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
    days: 30, // Use 30 days until backend is updated
    engine: null
  });

  // Trend viewer state
  const [timeBucket, setTimeBucket] = useState('weekly');
  const [selectedMetric, setSelectedMetric] = useState('extreme_mentions');
  const [trendData, setTrendData] = useState(null);

  // =============================================================================
  // CONFIGURATION
  // =============================================================================
  
  const engines = [
    { value: null, label: 'All Engines' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'perplexity', label: 'Perplexity' }
  ];

  const dayOptions = [
    { value: 7, label: 'Last Week' },
    { value: 30, label: 'Last Month' },
    { value: 90, label: 'Last 3 Months' },
    { value: 365, label: 'Full Year' }
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
      console.error('Error fetching data:', err);
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const getChartConfig = (chartData) => {
    const getMetricLabel = () => {
      switch (selectedMetric) {
        case 'extreme_mentions': return 'Extreme Mentions';
        case 'extreme_citations': return 'Extreme Citations';
        case 'avg_rank': return 'Avg Rank';
        default: return 'Value';
      }
    };

    const getMetricColor = () => {
      switch (selectedMetric) {
        case 'extreme_mentions': return '#3b82f6';
        case 'extreme_citations': return '#10b981';
        case 'avg_rank': return '#ef4444';
        default: return '#8b5cf6';
      }
    };

    return {
      data: {
        labels: chartData.labels,
        datasets: [
          {
            label: getMetricLabel(),
            data: chartData.data,
            borderColor: getMetricColor(),
            backgroundColor: getMetricColor() + '20',
            borderWidth: 3,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: getMetricColor(),
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 6,
            pointHoverRadius: 8,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#ffffff',
            bodyColor: '#ffffff',
            borderColor: getMetricColor(),
            borderWidth: 1,
            cornerRadius: 8,
            displayColors: false,
            callbacks: {
              title: (tooltipItems) => tooltipItems[0].label,
              label: (context) => `${getMetricLabel()}: ${context.parsed.y}`
            }
          }
        },
        scales: {
          x: {
            grid: {
              color: 'rgba(255, 255, 255, 0.1)',
              borderColor: 'rgba(255, 255, 255, 0.2)'
            },
            ticks: {
              color: 'rgba(255, 255, 255, 0.7)',
              font: {
                size: 11
              },
              maxRotation: 45
            }
          },
          y: {
            grid: {
              color: 'rgba(255, 255, 255, 0.1)',
              borderColor: 'rgba(255, 255, 255, 0.2)'
            },
            ticks: {
              color: 'rgba(255, 255, 255, 0.7)',
              font: {
                size: 12
              }
            },
            beginAtZero: selectedMetric === 'avg_rank' ? false : true
          }
        },
        interaction: {
          intersect: false,
          mode: 'index'
        },
        elements: {
          point: {
            hoverBackgroundColor: getMetricColor(),
            hoverBorderColor: '#ffffff'
          }
        }
      }
    };
  };

  const fetchTrendData = async () => {
    try {
      console.log('fetchTrendData called with:', { timeBucket, selectedMetric });
      
      // Call the new Extreme-focused trends endpoint
      const response = await fetch(`${API_BASE_URL}/metrics/extreme-trends?days=${timeBucket === 'weekly' ? 56 : 180}`);
      
      console.log('API response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const apiData = await response.json();
      console.log('API data received:', apiData);
      
      if (apiData && apiData.trends && apiData.trends.length > 0) {
                  // Filter out data points with zero values and the Aug 19 data point
          const validTrends = apiData.trends.filter(t => {
            let value = 0;
            switch (selectedMetric) {
              case 'extreme_mentions':
                value = t.extreme_mentions || 0;
                break;
              case 'extreme_citations':
                value = t.extreme_citations || 0;
                break;
              case 'avg_rank':
                value = t.avg_rank || 0;
                break;
              default:
                value = 0;
            }
            
            // Only include data points with actual values AND filter out Aug 19
            const date = new Date(t.date);
            const isAug19 = date.getMonth() === 7 && date.getDate() === 19; // August is month 7 (0-indexed)
            
            return value > 0 && !isAug19;
          });
          
          // If we only have one data point, ensure it's displayed prominently
          if (validTrends.length === 1) {
            console.log('Single data point detected:', validTrends[0]);
          }
        
        if (validTrends.length > 0) {
          // Transform backend data to chart format
          const chartData = {
            labels: validTrends.map(t => {
              const date = new Date(t.date);
              if (timeBucket === 'weekly') {
                return `Week of ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
              } else {
                return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
              }
            }),
            data: validTrends.map(t => {
              switch (selectedMetric) {
                case 'extreme_mentions':
                  return t.extreme_mentions || 0;
                case 'extreme_citations':
                  return t.extreme_citations || 0;
                case 'avg_rank':
                  return t.avg_rank || 0;
                default:
                  return 0;
              }
            })
          };
          
          const currentValue = chartData.data[chartData.data.length - 1] || 0;
          const previousValue = chartData.data[chartData.data.length - 2] || 0;
          
          // Handle single data point case
          let change = 0;
          let currentPeriod = chartData.labels[chartData.labels.length - 1] || 'Current';
          let previousPeriod = 'No previous data';
          
          if (validTrends.length === 1) {
            // Only one data point - show it as current with no change
            change = 0;
            previousPeriod = 'No previous data';
          } else if (validTrends.length > 1) {
            // Multiple data points - calculate change
            change = previousValue > 0 ? ((currentValue - previousValue) / previousValue * 100).toFixed(1) : 0;
            previousPeriod = chartData.labels[chartData.labels.length - 2] || 'Previous';
          }
          
          const trendData = {
            chartData: chartData,
            current_period: currentPeriod,
            previous_period: previousPeriod,
            change: parseFloat(change),
            metric: selectedMetric,
            time_bucket: timeBucket,
            current_value: currentValue,
            previous_value: previousValue
          };
          
          setTrendData(trendData);
        } else {
          // No valid trends found
          setTrendData(null);
        }
      } else {
        // Fallback to empty data if API doesn't return expected format
        setTrendData(null);
      }
    } catch (error) {
      console.error('Error fetching trend data:', error);
      // For now, show empty state - in production you'd want proper error handling
      setTrendData(null);
    }
  };

  // =============================================================================
  // TREND DATA EFFECTS
  // =============================================================================
  
  // Initial fetch on component mount
  useEffect(() => {
    console.log('Component mounted - initial trend data fetch');
    fetchTrendData();
  }, []); // Empty dependency array for initial fetch only

  useEffect(() => {
    console.log('useEffect triggered - fetching trend data for:', { timeBucket, selectedMetric });
    fetchTrendData();
  }, [timeBucket, selectedMetric]);

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
  
  // Safely extract data with proper null checks
  const analysis = data?.analysis || {};
  const citations = analysis.citations || {};
  const competitors = analysis.competitors || {};
  const entity_associations = analysis.entity_associations || {};
  const engine_breakdown = analysis.engine_breakdown || {};
  
  const totalRuns = data?.total_runs_analyzed || 0;
  
  // Calculate Extreme mentions from entity associations
  const extremeMentions = entity_associations?.total_products || 0;
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
          
          <div className="component-footer">
            <Link to="/metrics/query-overview" className="detail-link">
              View Detailed Analysis →
            </Link>
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
          
          <div className="component-footer">
            <Link to="/metrics/competitor-analysis" className="detail-link">
              View Detailed Analysis →
            </Link>
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
          
          <div className="component-footer">
            <Link to="/metrics/extreme-focus" className="detail-link">
              View Detailed Analysis →
            </Link>
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
          
          <div className="component-footer">
            <Link to="/metrics/citation-analysis" className="detail-link">
              View Detailed Analysis →
            </Link>
          </div>
        </div>
      </div>

      {/* =============================================================================
          TREND VIEWER
          ============================================================================= */}
      
      <div className="trend-viewer-section">
        <div className="trend-header">
          <h2>📈 Trend Viewer</h2>
          <p>Track key metrics over time with interactive charts</p>
        </div>
        
        <div className="trend-controls">
          <div className="control-group">
            <label>Time Bucket:</label>
            <select 
              value={timeBucket} 
              onChange={(e) => setTimeBucket(e.target.value)}
            >
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
          
          <div className="control-group">
            <label>Metric:</label>
            <select 
              value={selectedMetric} 
              onChange={(e) => setSelectedMetric(e.target.value)}
            >
              <option value="extreme_mentions">Extreme Mentions</option>
              <option value="extreme_citations">Extreme Citations</option>
              <option value="avg_rank">Avg Rank</option>
            </select>
          </div>
        </div>
        
        <div className="trend-chart-container">
          {trendData && trendData.chartData ? (
            <>
              <div className="chart-wrapper">
                <Line data={getChartConfig(trendData.chartData).data} options={getChartConfig(trendData.chartData).options} />
              </div>
              <div className="chart-stats">
                <div className="stat">
                  <span className="stat-label">Current Period:</span>
                  <span className="stat-value">{trendData.current_period}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Previous Period:</span>
                  <span className="stat-value">{trendData.previous_period}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Current Value:</span>
                  <span className="stat-value">{trendData.current_value}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Change:</span>
                  <span className={`stat-change ${trendData.change > 0 ? 'positive' : trendData.change < 0 ? 'negative' : 'neutral'}`}>
                    {trendData.change > 0 ? '+' : ''}{trendData.change === 0 ? 'No change' : `${trendData.change}%`}
                  </span>
                </div>
              </div>
            </>
          ) : (
            <div className="chart-placeholder">
              <div className="chart-info">
                <h3>Loading Chart...</h3>
                <p>Select time bucket and metric above to view trends</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MetricsDashboard;
