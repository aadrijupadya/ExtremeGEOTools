import React, { useEffect, useMemo, useState } from 'react';
import BrandIcon from './BrandIcon';
import { listRuns, deleteRun } from '../services/api';
import { Link } from 'react-router-dom';

function ResultsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [engineFilter, setEngineFilter] = useState('');
  const [modelFilter, setModelFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [timeRange, setTimeRange] = useState(''); // '', '24h', '7d', '30d'
  const [sortKey, setSortKey] = useState('ts');
  const [sortDir, setSortDir] = useState('desc');

  useEffect(() => {
    (async () => {
      setLoading(true);
      const data = await listRuns(200, 0);
      setItems(data.items || []);
      setLoading(false);
    })();
  }, []);

  const engines = useMemo(() => Array.from(new Set((items || []).map(r => r.engine))).sort(), [items]);
  const models = useMemo(() => Array.from(new Set((items || []).map(r => r.model).filter(Boolean))).sort(), [items]);

  const filtered = useMemo(() => {
    const term = (search || '').toLowerCase().trim();
    const now = Date.now();
    const since = (() => {
      if (timeRange === '24h') return now - 24 * 60 * 60 * 1000;
      if (timeRange === '7d') return now - 7 * 24 * 60 * 60 * 1000;
      if (timeRange === '30d') return now - 30 * 24 * 60 * 60 * 1000;
      return 0;
    })();

    return (items || []).filter(r => {
      if (engineFilter && r.engine !== engineFilter) return false;
      if (modelFilter && r.model !== modelFilter) return false;
      const isErr = (r.status || '').toLowerCase().startsWith('error');
      if (statusFilter === 'ok' && isErr) return false;
      if (statusFilter === 'error' && !isErr) return false;
      if (since) {
        const t = new Date(r.ts).getTime();
        if (isFinite(t) && t < since) return false;
      }
      if (!term) return true;
      const hay = [r.query, r.preview].join(' ').toLowerCase();
      return hay.includes(term);
    });
  }, [items, engineFilter, modelFilter, statusFilter, search, timeRange]);

  const sorted = useMemo(() => {
    const out = [...filtered];
    out.sort((a, b) => {
      let av = a[sortKey];
      let bv = b[sortKey];
      if (sortKey === 'ts') { av = new Date(a.ts).getTime(); bv = new Date(b.ts).getTime(); }
      if (sortKey === 'cost_usd') { av = Number(a.cost_usd || 0); bv = Number(b.cost_usd || 0); }
      if (typeof av === 'string') av = av.toLowerCase();
      if (typeof bv === 'string') bv = bv.toLowerCase();
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return out;
  }, [filtered, sortKey, sortDir]);

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir(prev => (prev === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir(key === 'ts' ? 'desc' : 'asc'); }
  };

  const exportToCSV = (data) => {
    if (!data || data.length === 0) {
      alert('No data to export');
      return;
    }

    const headers = ['When', 'Engine', 'Model', 'Status', 'Cost (USD)', 'Full Answer', 'Latency (ms)'];
    const csvContent = [
      headers.join(','),
      ...data.map(r => [
        `${new Date(r.ts).toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric'
        })} ${new Date(r.ts).toLocaleTimeString('en-US', { 
          hour: '2-digit', 
          minute: '2-digit',
          hour12: true 
        })}`,
        r.engine || '',
        r.model || '',
        r.status || '',
        Number(r.cost_usd || 0).toFixed(6),
        `"${(r.answer || r.preview || '').replace(/"/g, '""')}"`,
        r.latency_ms || ''
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `results_page_runs_export_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const StatusCell = ({ status }) => {
    const s = String(status || '').trim();
    const isErr = s.toLowerCase().startsWith('error');
    const errMsg = isErr ? s.split(':').slice(1).join(':').trim() : '';
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }} title={isErr ? errMsg : 'OK'}>
        <span className={`dot ${isErr ? 'err' : 'ok'}`} />
        <span>{isErr ? 'Error' : 'OK'}</span>
        {isErr && errMsg ? <span style={{ color: 'var(--error-fg, #ef4444)', fontSize: 12 }}>— {errMsg}</span> : null}
      </div>
    );
  };

  if (loading) return <div>Loading…</div>;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 10 }}>
        <h2 style={{ margin: 0 }}>Recent Runs</h2>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={() => exportToCSV(sorted)}
            style={{ 
              padding: '0.5rem 1rem', 
              borderRadius: 8, 
              border: '1px solid var(--accent, #667eea)', 
              background: 'var(--accent, #667eea)', 
              color: '#ffffff', 
              cursor: 'pointer',
              fontWeight: '500'
            }}
          >
            Export to CSV
          </button>
          <input
            type="text"
            placeholder="Search text…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ padding: '0.5rem 0.7rem', borderRadius: 8, border: '1px solid var(--border, #e5e7eb)', background: 'var(--card, #fff)', color: 'var(--text, #111)', minWidth: 200 }}
          />
          <select value={engineFilter} onChange={(e) => setEngineFilter(e.target.value)} style={{ padding: '0.5rem 0.7rem', borderRadius: 8, border: '1px solid var(--border, #e5e7eb)', background: 'var(--card, #fff)', color: 'var(--text, #111)' }}>
            <option value="">Engine</option>
            {engines.map(e => <option key={e} value={e}>{e}</option>)}
          </select>
          <select value={modelFilter} onChange={(e) => setModelFilter(e.target.value)} style={{ padding: '0.5rem 0.7rem', borderRadius: 8, border: '1px solid var(--border, #e5e7eb)', background: 'var(--card, #fff)', color: 'var(--text, #111)' }}>
            <option value="">Model</option>
            {models.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ padding: '0.5rem 0.7rem', borderRadius: 8, border: '1px solid var(--border, #e5e7eb)', background: 'var(--card, #fff)', color: 'var(--text, #111)' }}>
            <option value="">Status</option>
            <option value="ok">ok</option>
            <option value="error">error</option>
          </select>
          <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)} style={{ padding: '0.5rem 0.7rem', borderRadius: 8, border: '1px solid var(--border, #e5e7eb)', background: 'var(--card, #fff)', color: 'var(--text, #111)' }}>
            <option value="">Any time</option>
            <option value="24h">Last 24h</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
        </div>
      </div>

      <table width="100%" cellPadding="6" style={{ borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th align="left" style={{ cursor: 'pointer' }} onClick={() => toggleSort('ts')}>When {sortKey==='ts' ? (sortDir==='asc'?'▲':'▼') : ''}</th>
            <th align="left" style={{ cursor: 'pointer' }} onClick={() => toggleSort('engine')}>Engine {sortKey==='engine' ? (sortDir==='asc'?'▲':'▼') : ''}</th>
            <th align="left" style={{ cursor: 'pointer' }} onClick={() => toggleSort('model')}>Model {sortKey==='model' ? (sortDir==='asc'?'▲':'▼') : ''}</th>
            <th align="left">Status</th>
            <th align="right" style={{ cursor: 'pointer' }} onClick={() => toggleSort('cost_usd')}>Cost {sortKey==='cost_usd' ? (sortDir==='asc'?'▲':'▼') : ''}</th>
            <th align="left">Preview</th>
            <th align="right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((r) => (
            <tr key={r.id}>
              <td>{new Date(r.ts).toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric'
              })} {new Date(r.ts).toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: true 
              })}</td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <BrandIcon name={(r.engine || '').toLowerCase()} size={14} />
                  <span>{r.engine}</span>
                </div>
              </td>
              <td>{r.model}</td>
              <td><StatusCell status={r.status} /></td>
              <td align="right">${Number(r.cost_usd || 0).toFixed(6)}</td>
              <td>
                <Link 
                  to={`/runs/${encodeURIComponent(r.id)}`}
                  style={{ 
                    color: 'var(--accent, #667eea)', 
                    textDecoration: 'none',
                    fontWeight: '500'
                  }}
                >
                  {r.preview}
                </Link>
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
                  style={{ border: '1px solid #ef4444', color: '#ffffff', background: '#ef4444', padding: '4px 8px', borderRadius: 6 }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr><td colSpan={7} style={{ color: '#666', padding: '1rem' }}>No matching runs</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default ResultsPage;


