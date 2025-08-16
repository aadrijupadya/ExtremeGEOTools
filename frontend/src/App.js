import React, { useState } from 'react';
import Header from './components/Header';
import QueryForm from './components/QueryForm';
import ResultsTable from './components/ResultsTable';
import Dashboard from './components/Dashboard';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './components/Home';
import QueryPage from './components/QueryPage';
import CostsPage from './components/CostsPage';
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
    // Update the results state with new query data
    setQueryResults(prevResults => [...prevResults, ...results.runs]);
  };

  return (
    <Router>
      <div className="App">
        <Header />
        <nav style={{ padding: '0.5rem 1rem' }}>
          <Link to="/" style={{ marginRight: '1rem' }}>Home</Link>
          <Link to="/query" style={{ marginRight: '1rem' }}>Query</Link>
          <Link to="/costs">Costs</Link>
        </nav>
        <div className="container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/query" element={<QueryPage onSubmit={handleQuerySubmit} onResults={handleQueryResults} isLoading={isLoading} />} />
            <Route path="/costs" element={<CostsPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
