import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { API_BASE_URL, streamQuery } from '../services/api';

function RunLivePage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [runId, setRunId] = useState(null);
  const [err, setErr] = useState(null);
  const esRef = useRef(null);

  useEffect(() => {
    const q = searchParams.get('q') || '';
    const model = searchParams.get('model') || '';
    const intent = searchParams.get('intent') || 'unlabeled';
    const temperature = parseFloat(searchParams.get('t') || '0.2');
    const engine = (searchParams.get('engine') || 'openai').toLowerCase();
    if (!q) {
      setErr('No query provided');
      return;
    }
    let es;
    if (engine === 'perplexity' || engine === 'pplx') {
      const url = new URL(`${API_BASE_URL}/query/stream`);
      url.searchParams.set('query', q);
      url.searchParams.set('engine', 'perplexity');
      if (model) url.searchParams.set('model', model);
      if (intent) url.searchParams.set('intent', intent);
      url.searchParams.set('temperature', String(temperature));
      es = new EventSource(url.toString());
    } else {
      es = streamQuery({ query: q, model, intent, temperature });
    }
    esRef.current = es;
    es.addEventListener('start', (e) => {
      try {
        const data = JSON.parse(e.data || '{}');
        if (data.run_id) setRunId(data.run_id);
      } catch {}
    });
    es.addEventListener('delta', (e) => {
      try {
        const data = JSON.parse(e.data || '{}');
        if (data.text) setText((prev) => prev + data.text);
      } catch {}
    });
    es.addEventListener('done', (e) => {
      try {
        const data = JSON.parse(e.data || '{}');
        const id = data.run_id || runId;
        if (id) navigate(`/runs/${encodeURIComponent(id)}`);
      } catch {
        if (runId) navigate(`/runs/${encodeURIComponent(runId)}`);
      }
    });
    es.addEventListener('error', (e) => {
      try {
        const data = JSON.parse(e.data || '{}');
        setErr(data.message || 'Stream error');
        console.error('Stream error:', data);
      } catch {
        setErr('Stream error');
        console.error('Stream error: unknown');
      }
    });
    es.onerror = (e) => {
      // Network or server-side end
      // Keep minimal handling; SSE errors also flow via 'error' event above when JSON provided
    };
    return () => {
      try { es.close(); } catch {}
    };
  }, []);

  return (
    <div>
      <h2>Generating…</h2>
      {err && <div style={{ color: '#b91c1c', marginBottom: 8 }}>{err}</div>}
      <div style={{ whiteSpace: 'pre-wrap', background: 'var(--card, #fafafa)', padding: '0.75rem', borderRadius: 8, minHeight: 160 }}>
        {text || 'Waiting for first tokens…'}
      </div>
      <div style={{ color: '#666', marginTop: 8 }}>
        {runId ? `Run ID: ${runId}` : 'Preparing run…'}
      </div>
    </div>
  );
}

export default RunLivePage;


