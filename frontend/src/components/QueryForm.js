import React, { useState } from 'react';
import BrandIcon from './BrandIcon';
import { runQuery, lookupRuns } from '../services/api';
import { useNavigate } from 'react-router-dom';

function QueryForm({ onSubmit, onResults, isLoading, onDraftChange, initialDraft }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState(initialDraft?.text ?? '');
  const [engines, setEngines] = useState(initialDraft?.engines ?? ['openai']);
  const [intent, setIntent] = useState(initialDraft?.intent ?? 'commercial');
  const [temperature, setTemperature] = useState(initialDraft?.temperature ?? 0.2);
  const [openaiModel, setOpenaiModel] = useState(initialDraft?.openai_model ?? initialDraft?.model ?? 'gpt-4o-search-preview');
  const [pplxModel, setPplxModel] = useState(initialDraft?.perplexity_model ?? 'sonar');
  const [cacheCandidate, setCacheCandidate] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    const selectedEngine = (engines && engines.length > 0) ? engines[0] : 'openai';
    const queryData = {
      query: query.trim(),
      engines: engines,
      intent: intent,
      temperature: Number(temperature),
      // legacy field for compatibility
      model: openaiModel,
      // new per-engine model fields
      openai_model: openaiModel,
      perplexity_model: pplxModel,
    };

    try {
      // Pre-check cache for same-day runs and offer a smooth inline choice
      const pre = await lookupRuns({ query: queryData.query, engines });
      const existing = (pre?.matches || [])[0];
      if (existing && existing.id) {
        setCacheCandidate(existing);
        return; // Wait for user action (open cached or run anyway)
      }

      // Streaming for OpenAI/Perplexity
      if (selectedEngine === 'openai') {
        const url = `/live?q=${encodeURIComponent(queryData.query)}&model=${encodeURIComponent(openaiModel)}&t=${encodeURIComponent(String(queryData.temperature))}&intent=${encodeURIComponent(intent)}&engine=openai`;
        navigate(url);
        return;
      }
      if (selectedEngine === 'perplexity') {
        const url = `/live?q=${encodeURIComponent(queryData.query)}&model=${encodeURIComponent(pplxModel)}&t=${encodeURIComponent(String(queryData.temperature))}&intent=${encodeURIComponent(intent)}&engine=perplexity`;
        navigate(url);
        return;
      }

      const result = await runQuery(queryData);
      onSubmit(result);
      onResults(result); // Pass results to parent component
      setQuery(''); // Clear form after successful submission
    } catch (error) {
      console.error('Query failed:', error);
      // You can add error handling here
    }
  };

  const handleEngineChange = (engine) => {
    if (engines.includes(engine)) {
      setEngines(engines.filter(e => e !== engine));
    } else {
      setEngines([...engines, engine]);
    }
  };

  // Notify parent on draft changes for live estimation panel
  React.useEffect(() => {
    if (typeof onDraftChange === 'function') {
      onDraftChange({ text: query, engines, intent, temperature, openai_model: openaiModel, perplexity_model: pplxModel });
    }
    // Hide cache banner when the query text or engines change
    setCacheCandidate(null);
  }, [query, engines, intent, temperature, openaiModel, pplxModel]);

  // Show temperature slider if Perplexity is selected, or if OpenAI model supports it (gpt-5*)
  const isOpenAI = engines.includes('openai') && (!engines.includes('perplexity') || engines[0] === 'openai');
  const isPPLX = engines.includes('perplexity') && (!engines.includes('openai') || engines[0] === 'perplexity');
  const showTemp = (isPPLX) || (isOpenAI && (openaiModel || '').startsWith('gpt-5'));

  return (
    <div className="query-form">
      {cacheCandidate && (
        <div
          style={{
            marginBottom: '12px',
            padding: '12px 14px',
            border: '1px solid #e6e6e6',
            borderRadius: 10,
            background: '#f9fbff',
            boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
            transition: 'all 200ms ease-in-out'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
            <div>
              <div style={{ fontWeight: 600 }}>Found a result from earlier today</div>
              <div style={{ color: '#666', fontSize: 13 }}>
                We detected a similar query already run today. You can open that result or run a fresh query.
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                type="button"
                onClick={() => navigate(`/runs/${encodeURIComponent(cacheCandidate.id)}`)}
                style={{
                  padding: '8px 12px',
                  borderRadius: 8,
                  border: '1px solid #cbd5e1',
                  background: 'white',
                  cursor: 'pointer'
                }}
              >
                Open cached
              </button>
              <button
                type="button"
                onClick={async () => {
                  const selectedEngine = (engines && engines.length > 0) ? engines[0] : 'openai';
                  if (selectedEngine === 'openai') {
                    const url = `/live?q=${encodeURIComponent(query.trim())}&model=${encodeURIComponent(openaiModel)}&t=${encodeURIComponent(String(temperature))}&intent=${encodeURIComponent(intent)}&engine=openai`;
                    navigate(url);
                    setCacheCandidate(null);
                    return;
                  } else if (selectedEngine === 'perplexity') {
                    const url = `/live?q=${encodeURIComponent(query.trim())}&model=${encodeURIComponent(pplxModel)}&t=${encodeURIComponent(String(temperature))}&intent=${encodeURIComponent(intent)}&engine=perplexity`;
                    navigate(url);
                    setCacheCandidate(null);
                    return;
                  }
                  const queryData = {
                    query: query.trim(),
                    engines: engines,
                    intent: intent,
                    temperature: Number(temperature),
                    model: openaiModel,
                    openai_model: openaiModel,
                    perplexity_model: pplxModel,
                  };
                  try {
                    const result = await runQuery(queryData);
                    onSubmit(result);
                    onResults(result);
                    setQuery('');
                  } catch (err) {
                    console.error('Query failed:', err);
                  } finally {
                    setCacheCandidate(null);
                  }
                }}
                style={{
                  padding: '8px 12px',
                  borderRadius: 8,
                  border: '1px solid #3b82f6',
                  background: '#3b82f6',
                  color: 'white',
                  cursor: 'pointer'
                }}
              >
                Run anyway
              </button>
            </div>
          </div>
        </div>
      )}
      <h2>Run Competitive Intelligence Query</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="query">Query:</label>
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your competitive intelligence query..."
            rows="3"
            required
          />
        </div>

        <div className="form-group">
          <label>AI Engine:</label>
          <div className="checkbox-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                type="radio"
                name="engine"
                checked={engines.length === 1 && engines[0] === 'openai'}
                onChange={() => setEngines(['openai'])}
              />
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <BrandIcon name="chatgpt" size={16} /> OpenAI
              </span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                type="radio"
                name="engine"
                checked={engines.length === 1 && engines[0] === 'perplexity'}
                onChange={() => setEngines(['perplexity'])}
              />
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <BrandIcon name="perplexity" size={16} /> Perplexity (Web Search)
              </span>
            </label>
          </div>
        </div>

        {engines.includes('openai') && (
          <div className="form-group">
            <label htmlFor="model">OpenAI Model:</label>
            <select id="model" value={openaiModel} onChange={(e) => setOpenaiModel(e.target.value)}>
              <option value="gpt-4o-search-preview">GPT-4o (search preview) — default</option>
              <option value="gpt-5-mini">GPT-5 mini</option>
            </select>
          </div>
        )}

        {engines.includes('perplexity') && (
          <div className="form-group">
            <label htmlFor="pplx-model">Perplexity Model:</label>
            <select id="pplx-model" value={pplxModel} onChange={(e) => setPplxModel(e.target.value)}>
              <option value="sonar">sonar (default)</option>
              <option value="sonar-pro">sonar-pro</option>
              <option value="sonar-reasoning">sonar-reasoning</option>
            </select>
          </div>
        )}

        {showTemp && (
          <div className="form-group">
            <label htmlFor="temperature">Temperature: {Number(temperature).toFixed(1)}</label>
            <input
              id="temperature"
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(e.target.value)}
            />
          </div>
        )}

        <button 
          type="submit" 
          disabled={isLoading || !query.trim()}
          className="submit-btn"
        >
          {isLoading ? 'Running Query...' : 'Run Query'}
        </button>
      </form>
    </div>
  );
}

export default QueryForm;
