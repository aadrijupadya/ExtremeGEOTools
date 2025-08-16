import React, { useState } from 'react';
import { runQuery } from '../services/api';

function QueryForm({ onSubmit, onResults, isLoading, onDraftChange, initialDraft }) {
  const [query, setQuery] = useState(initialDraft?.text ?? '');
  const [engines, setEngines] = useState(initialDraft?.engines ?? ['openai']);
  const [intent, setIntent] = useState(initialDraft?.intent ?? 'commercial');
  const [temperature, setTemperature] = useState(initialDraft?.temperature ?? 0.2);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    const queryData = {
      query: query.trim(),
      engines: engines,
      intent: intent,
      temperature: Number(temperature)
    };

    try {
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
      onDraftChange({ text: query, engines, intent, temperature });
    }
  }, [query, engines, intent, temperature]);

  return (
    <div className="query-form">
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
          <label>AI Engines:</label>
          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={engines.includes('openai')}
                onChange={() => handleEngineChange('openai')}
              />
              OpenAI (GPT-4o)
            </label>
            <label>
              <input
                type="checkbox"
                checked={engines.includes('perplexity')}
                onChange={() => handleEngineChange('perplexity')}
              />
              Perplexity (Web Search)
            </label>
          </div>
        </div>

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
