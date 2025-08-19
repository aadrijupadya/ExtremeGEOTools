import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getRun } from '../services/api';

function escapeHtml(s) {
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
}

function formatMarkdownLite(s) {
  let out = escapeHtml(s || '');
  // Bold: **text** => <strong>text</strong>
  out = out.replace(/\*\*(.+?)\*\*/gms, '<strong>$1</strong>');
  // Markdown links: [title](url)
  out = out.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/gms, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');
  // Raw URLs
  out = out.replace(/(https?:\/\/[\w\-._~:?#\[\]@!$&'()*+,;=%/]+)(?![^<]*>)/gms, '<a href="$1" target="_blank" rel="noreferrer">$1</a>');
  // Preserve line breaks
  out = out.replace(/\n/g, '<br/>');
  return out;
}

function RunDetailPage() {
  const { id } = useParams();
  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await getRun(id);
        setRun(data);
      } catch (e) {
        setErr('Failed to load run');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) return <div>Loading…</div>;
  if (err) return <div>{err}</div>;
  if (!run) return <div>Not found</div>;

  const answerHtml = formatMarkdownLite(run.raw_excerpt || '');

  return (
    <div>
      <p><Link to="/results">← Back to results</Link></p>
      <h2>Run {run.id}</h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1rem', alignItems: 'start' }}>
        <div>
          <h3>Answer</h3>
          <div style={{ background: 'var(--card, #0e1320)', color: 'var(--text, #111)', padding: '1rem 1.1rem', borderRadius: 12, border: '1px solid var(--border, #e5e7eb)', lineHeight: 1.6 }}
               dangerouslySetInnerHTML={{ __html: answerHtml }} />

          <h3 style={{ marginTop: '1rem' }}>Citations</h3>
          <ul>
            {Array.isArray(run.citations) && run.citations.length > 0 ? (
              run.citations.map((c) => (
                <li key={c.url}>
                  <a href={c.url} target="_blank" rel="noreferrer">{c.title || c.url}</a>
                  {c.domain ? <span style={{ color: '#666' }}> ({c.domain})</span> : null}
                </li>
              ))
            ) : (
              <li style={{ color: '#666' }}>No links</li>
            )}
          </ul>

          <h3>Entities</h3>
          <div>
            {Array.isArray(run.vendors) && run.vendors.length > 0 ? run.vendors.map((v, i) => (
              <span key={`${v?.name || 'v'}-${i}`} style={{ display: 'inline-block', marginRight: 8, marginBottom: 8, padding: '4px 8px', border: '1px solid var(--border, #ddd)', borderRadius: 12 }}>
                {v?.name || 'unknown'}
              </span>
            )) : <span style={{ color: '#666' }}>No entities</span>}
          </div>
        </div>

        <aside style={{ border: '1px solid var(--border, #ddd)', padding: '0.75rem', borderRadius: 12, display: 'flex', flexDirection: 'column', justifyContent: 'center', minHeight: 220 }}>
          <h3 style={{ marginTop: 0, marginBottom: 8 }}>Meta</h3>
          <div style={{ display: 'grid', rowGap: 6 }}>
            <div><strong>When</strong>: {new Date(run.ts).toLocaleString()}</div>
            <div><strong>Engine</strong>: {run.engine}</div>
            <div><strong>Model</strong>: {run.model}</div>
            <div><strong>Status</strong>: {run.status}</div>
            <div><strong>Latency</strong>: {run.latency_ms} ms</div>
            <div><strong>Tokens</strong>: in {run.input_tokens}, out {run.output_tokens}</div>
            <div><strong>Cost</strong>: ${Number(run.cost_usd || 0).toFixed(6)}</div>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default RunDetailPage;


