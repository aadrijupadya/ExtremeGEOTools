import React from 'react';
import Header from './components/Header';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './components/Home';
import QueryPage from './components/QueryPage';
import CostsPage from './components/CostsPage';
import ResultsPage from './components/ResultsPage';
import RunDetailPage from './components/RunDetailPage';
import RunLivePage from './components/RunLivePage';
import MetricsDashboard from './components/MetricsDashboard';
import QueryOverviewDetail from './components/QueryOverviewDetail';
import CompetitorAnalysisDetail from './components/CompetitorAnalysisDetail';
import ExtremeFocusDetail from './components/ExtremeFocusDetail';
import CitationAnalysisDetail from './components/CitationAnalysisDetail';
import './styles/App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <div className="container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/query" element={<QueryPage />} />
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
            <Route path="/metrics/extreme-focus" element={<ExtremeFocusDetail />} />
            <Route path="/metrics/citation-analysis" element={<CitationAnalysisDetail />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
