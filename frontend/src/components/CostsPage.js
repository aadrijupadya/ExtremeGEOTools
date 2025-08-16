import React, { useEffect, useState } from 'react';
import { getCostsStats } from '../services/api';

function Currency({ value }) {
  return <span>${Number(value || 0).toFixed(6)}</span>;
}

function CostsPage() {
  const [stats, setStats] = useState({ total_cost_usd: 0, total_runs: 0, by_engine: {}, by_model: {} });

  useEffect(() => {
    (async () => {
      const s = await getCostsStats();
      setStats(s || { total_cost_usd: 0, total_runs: 0, by_engine: {}, by_model: {} });
    })();
  }, []);

  return (
    <div>
      <h2>Costs</h2>
      <div style={{ display: 'flex', gap: '2rem', marginBottom: '1rem' }}>
        <div><strong>Total runs:</strong> {stats.total_runs}</div>
        <div><strong>Total cost:</strong> <Currency value={stats.total_cost_usd} /></div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div>
          <h3>By Engine</h3>
          <table width="100%" cellPadding="6" style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th align="left">Engine</th>
                <th align="right">Runs</th>
                <th align="right">Cost</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(stats.by_engine || {}).map(([eng, v]) => (
                <tr key={eng}>
                  <td>{eng}</td>
                  <td align="right">{v.runs}</td>
                  <td align="right"><Currency value={v.cost} /></td>
                </tr>
              ))}
              {Object.keys(stats.by_engine || {}).length === 0 && (
                <tr><td colSpan={3} style={{ color: '#666' }}>No data yet</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <div>
          <h3>By Model</h3>
          <table width="100%" cellPadding="6" style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th align="left">Model</th>
                <th align="right">Runs</th>
                <th align="right">Cost</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(stats.by_model || {}).map(([model, v]) => (
                <tr key={model}>
                  <td>{model}</td>
                  <td align="right">{v.runs}</td>
                  <td align="right"><Currency value={v.cost} /></td>
                </tr>
              ))}
              {Object.keys(stats.by_model || {}).length === 0 && (
                <tr><td colSpan={3} style={{ color: '#666' }}>No data yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default CostsPage;


