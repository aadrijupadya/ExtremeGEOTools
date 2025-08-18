import React, { useState } from 'react';
import { runQuery, lookupRuns } from '../services/api';
import { useNavigate } from 'react-router-dom';

function QueryForm({ onSubmit, onResults, isLoading, onDraftChange, initialDraft }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState(initialDraft?.text ?? '');
  const [engines, setEngines] = useState(initialDraft?.engines ?? ['openai']);
  const [intent, setIntent] = useState(initialDraft?.intent ?? 'commercial');
  const [temperature, setTemperature] = useState(initialDraft?.temperature ?? 0.2);
  const [model, setModel] = useState(initialDraft?.model ?? 'gpt-5-nano-2025-08-07');
  const [cacheCandidate, setCacheCandidate] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    const queryData = {
      query: query.trim(),
      engines: engines,
      intent: intent,
      temperature: Number(temperature),
      model
    };

    try {
      // Pre-check cache for same-day runs and offer a smooth inline choice
      const pre = await lookupRuns({ query: queryData.query, engines });
      const existing = (pre?.matches || [])[0];
      if (existing && existing.id) {
        setCacheCandidate(existing);
        return; // Wait for user action (open cached or run anyway)
      }

      const result = await runQuery(queryData);
      console.log("Click Registered");
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
      onDraftChange({ text: query, engines, intent, temperature, model });
    }
    // Hide cache banner when the query text or engines change
    setCacheCandidate(null);
  }, [query, engines, intent, temperature, model]);

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
                  const queryData = {
                    query: query.trim(),
                    engines: engines,
                    intent: intent,
                    temperature: Number(temperature)
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
            <label>
              <input
                type="radio"
                name="engine"
                checked={engines.length === 1 && engines[0] === 'openai'}
                onChange={() => setEngines(['openai'])}
              />
              OpenAI
            </label>
            <label>
              <input
                type="radio"
                name="engine"
                checked={engines.length === 1 && engines[0] === 'perplexity'}
                onChange={() => setEngines(['perplexity'])}
              />
              Perplexity (Web Search)
            </label>
          </div>
        </div>

        {engines.includes('openai') && (
          <div className="form-group">
            <label htmlFor="model">OpenAI Model:</label>
            <select id="model" value={model} onChange={(e) => setModel(e.target.value)}>
              <option value="gpt-5-nano-2025-08-07">GPT-5 nano (fastest)</option>
              <option value="gpt-5-mini-2025-08-07">GPT-5 mini</option>
              <option value="gpt-4o-mini-search-preview-2025-03-11">GPT-4o mini (search preview)</option>
            </select>
          </div>
        )}

        {engines.includes('perplexity') && (
          <div className="form-group">
            <label htmlFor="pplx-model">Perplexity Model:</label>
            <select id="pplx-model" value={model} onChange={(e) => setModel(e.target.value)}>
              <option value="sonar">sonar (default)</option>
              <option value="sonar-pro">sonar-pro</option>
              <option value="sonar-reasoning">sonar-reasoning</option>
            </select>
          </div>
        )}

        <div className="form-group">
          <label htmlFor="intent">Intent:</label>
          <select
            id="intent"
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
          >
            <option value="commercial">Commercial</option>
            <option value="technical">Technical</option>
            <option value="market_research">Market Research</option>
            <option value="product_research">Product Research</option>
          </select>
        </div>

        {(!engines.includes('openai') || (model && !model.startsWith('gpt-5'))) && (
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
