import React, { useEffect, useState } from 'react';
import { listRuns, deleteRun } from '../services/api';
import { Link } from 'react-router-dom';

function ResultsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const data = await listRuns(50, 0);
      setItems(data.items || []);
      setLoading(false);
    })();
  }, []);

  if (loading) return <div>Loading…</div>;

  return (
    <div>
      <h2>Recent Runs</h2>
      <table width="100%" cellPadding="6" style={{ borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th align="left">When</th>
            <th align="left">Engine</th>
            <th align="left">Model</th>
            <th align="left">Status</th>
            <th align="right">Cost</th>
            <th align="left">Preview</th>
            <th align="right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((r) => (
            <tr key={r.id}>
              <td>{new Date(r.ts).toLocaleString()}</td>
              <td>{r.engine}</td>
              <td>{r.model}</td>
              <td>{r.status}</td>
              <td align="right">${Number(r.cost_usd || 0).toFixed(6)}</td>
              <td>
                <Link to={`/runs/${encodeURIComponent(r.id)}`}>{r.preview}</Link>
              </td>
              <td align="right">
                <button
                  title="Delete"
                  onClick={async () => {
                    if (!window.confirm('Remove this run from the list? Cost totals remain.')) return;
                    try {
                      await deleteRun(r.id);
                      setItems((prev) => prev.filter((x) => x.id !== r.id));
                    } catch (e) {
                      alert('Failed to delete run');
                    }
                  }}
                  style={{ border: '1px solid #ef4444', color: '#ef4444', background: 'white', padding: '4px 8px', borderRadius: 6 }}
                >
                  ✕
                </button>
              </td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr><td colSpan={6} style={{ color: '#666' }}>No runs yet</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default ResultsPage;


