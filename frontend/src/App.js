import React, { useState } from 'react';
import Header from './components/Header';
import QueryForm from './components/QueryForm';
import ResultsTable from './components/ResultsTable';
import Dashboard from './components/Dashboard';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './components/Home';
import QueryPage from './components/QueryPage';
import CostsPage from './components/CostsPage';
import ResultsPage from './components/ResultsPage';
import RunDetailPage from './components/RunDetailPage';
import RunLivePage from './components/RunLivePage';
import MetricsDashboard from './components/MetricsDashboard';
import QueryOverviewDetail from './components/QueryOverviewDetail';
import CompetitorAnalysisDetail from './components/CompetitorAnalysisDetail';
import './styles/App.css';

function App() {
  const [queryResults, setQueryResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleQuerySubmit = async (queryData) => {
    setIsLoading(true);
    try {
      // QueryForm will handle the API call and pass results here
      // We'll update the results here when QueryForm calls this
    } catch (error) {
      console.error('Query failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQueryResults = (results) => {
    setQueryResults(prevResults => [...prevResults, ...results.runs]);
  };

  return (
    <Router>
      <div className="App">
        <Header />
        <div className="container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/query" element={<QueryPage onSubmit={handleQuerySubmit} onResults={handleQueryResults} isLoading={isLoading} />} />
            <Route path="/costs" element={<CostsPage />} />
            <Route path="/results" element={<ResultsPage />} />
            <Route path="/runs/:id" element={<RunDetailPage />} />
            <Route path="/live" element={<RunLivePage />} />
            <Route path="/metrics" element={<MetricsDashboard />} />
            
            {/* =============================================================================
                DETAILED METRICS ENDPOINTS
                ============================================================================= */}
            <Route path="/metrics/query-overview" element={<QueryOverviewDetail />} />
            <Route path="/metrics/competitor-analysis" element={<CompetitorAnalysisDetail />} />
            <Route path="/metrics/extreme-focus" element={<div>Extreme Focus Detail - Coming Soon</div>} />
            <Route path="/metrics/citation-analysis" element={<div>Citation Analysis Detail - Coming Soon</div>} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
