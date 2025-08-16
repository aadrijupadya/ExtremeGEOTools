import React, { useState } from 'react';

function ResultsTable({ results }) {
  const [expandedId, setExpandedId] = useState(null);

  const toggleExpanded = (id) => {
    setExpandedId(prev => (prev === id ? null : id));
  };
  if (!results || results.length === 0) {
    return (
      <div className="results-table">
        <h3>Query Results</h3>
        <p>No results to display. Run a query to see results here.</p>
      </div>
    );
  }

  return (
    <div className="results-table">
      <h3>Query Results</h3>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Query</th>
              <th>Engine</th>
              <th>Status</th>
              <th>Cost</th>
              <th>Vendors Found</th>
              <th>Extreme Rank</th>
              <th>Timestamp</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {results.map((result) => (
              <React.Fragment key={result.id || `${result.engine}-${result.ts}`}>
                <tr>
                  <td>{result.query}</td>
                  <td>{result.engine}</td>
                  <td>
                    <span className={`status ${result.status}`}>
                      {result.status}
                    </span>
                  </td>
                  <td>${(result.cost_usd ?? 0).toFixed ? result.cost_usd.toFixed(6) : Number(result.cost_usd || 0).toFixed(6)}</td>
                  <td>{result.vendors?.length || 0}</td>
                  <td>{result.extreme_rank || 'N/A'}</td>
                  <td>{new Date(result.ts).toLocaleString()}</td>
                  <td>
                    <button onClick={() => toggleExpanded(result.id)}>
                      {expandedId === result.id ? 'Hide' : 'Show'}
                    </button>
                  </td>
                </tr>
                {expandedId === result.id && (
                  <tr>
                    <td colSpan={8}>
                      <div className="result-details">
                        <div className="excerpt">
                          <strong>Excerpt:</strong>
                          <div style={{ whiteSpace: 'pre-wrap' }}>{result.raw_excerpt || 'No excerpt available.'}</div>
                        </div>
                        <div className="vendors" style={{ marginTop: '8px' }}>
                          <strong>Vendors:</strong>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                            {(result.vendors || []).map((v, idx) => (
                              <span key={idx} style={{ padding: '2px 8px', border: '1px solid #ccc', borderRadius: '12px' }}>{v.name}</span>
                            ))}
                          </div>
                        </div>
                        <div className="links" style={{ marginTop: '8px' }}>
                          <strong>Links:</strong>
                          <ul style={{ marginTop: '4px' }}>
                            {(result.links || []).map((link, idx) => (
                              <li key={idx}>
                                <a href={link} target="_blank" rel="noreferrer noopener">{link}</a>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ResultsTable;

