import React, { useState } from 'react';
import ResultsTable from './ResultsTable';
import Scheduler from './Scheduler';

function Dashboard({ queryResults, isLoading }) {
  const [filteredResults, setFilteredResults] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  // Filter results based on search term
  React.useEffect(() => {
    if (searchTerm) {
      const filtered = queryResults.filter(result =>
        result.query.toLowerCase().includes(searchTerm.toLowerCase()) ||
        result.engine.toLowerCase().includes(searchTerm.toLowerCase()) ||
        result.intent.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredResults(filtered);
    } else {
      setFilteredResults(queryResults);
    }
  }, [queryResults, searchTerm]);

  const exportToCSV = () => {
    if (filteredResults.length === 0) return;

    const headers = ['Query', 'Engine', 'Status', 'Cost', 'Vendors Found', 'Extreme Rank', 'Timestamp'];
    const csvContent = [
      headers.join(','),
      ...filteredResults.map(result => [
        `"${result.query}"`,
        result.engine,
        result.status,
        result.cost_usd || 0,
        result.vendors?.length || 0,
        result.extreme_rank || 'N/A',
        result.ts
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `competitive-intelligence-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const getTotalCost = () => {
    return filteredResults.reduce((total, result) => total + (result.cost_usd || 0), 0);
  };

  const getTotalQueries = () => filteredResults.length;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Competitive Intelligence Dashboard</h2>
        <div className="dashboard-stats">
          <div className="stat">
            <span className="stat-label">Total Queries:</span>
            <span className="stat-value">{getTotalQueries()}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Total Cost:</span>
            <span className="stat-value">${getTotalCost().toFixed(6)}</span>
          </div>
        </div>
      </div>

      {/* Query Scheduler Section */}
      <Scheduler />

      <div className="dashboard-controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search queries, engines, or intent..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <button 
          onClick={exportToCSV} 
          disabled={filteredResults.length === 0}
          className="export-btn"
        >
          Export to CSV
        </button>
      </div>

      <ResultsTable results={filteredResults} />
    </div>
  );
}

export default Dashboard;

