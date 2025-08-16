import React, { useEffect, useMemo, useRef, useState } from 'react';
import QueryForm from './QueryForm';
import { getPricingModels } from '../services/api';
import { usePersistentDraft } from '../hooks/usePersistentDraft';

function estimateTokensFromText(text) {
  const chars = (text || '').length;
  return Math.ceil(chars / 4); // simple heuristic
}

function QueryPage({ onSubmit, onResults, isLoading }) {
  const [pricing, setPricing] = useState({ models: [], defaults: { input_per_1k: 0.0025, output_per_1k: 0.01 } });
  const { loadDraft, saveDraft, clearDraft } = usePersistentDraft('egt.queryDraft.v1');
  const initial = loadDraft() || { text: '', engines: ['openai'], intent: 'commercial', temperature: 0.2 };
  const [draft, setDraft] = useState(initial);
  const saveTimer = useRef(null);

  useEffect(() => {
    (async () => {
      const p = await getPricingModels();
      setPricing(p || { models: [], defaults: { input_per_1k: 0.0025, output_per_1k: 0.01 } });
    })();
  }, []);

  // Debounced autosave to localStorage
  useEffect(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      saveDraft(draft);
    }, 300);
    return () => saveTimer.current && clearTimeout(saveTimer.current);
  }, [draft]);

  const activeModel = useMemo(() => {
    const engines = draft.engines || ['openai'];
    const engine = engines.includes('openai') ? 'openai' : engines[0] || 'openai';
    // default model per engine
    const model = engine === 'perplexity' ? 'sonar' : 'gpt-4o';
    const m = (pricing.models || []).find(x => x.id === model);
    return m || { id: model, input_per_1k: pricing.defaults?.input_per_1k || 0.0025, output_per_1k: pricing.defaults?.output_per_1k || 0.01 };
  }, [draft.engines, pricing]);

  const estimate = useMemo(() => {
    const inputTokens = estimateTokensFromText(draft.text || '');
    const inputCostPer1k = activeModel.input_per_1k || 0.0025;
    const estimatedCost = (inputTokens / 1000.0) * inputCostPer1k;
    return { inputTokens, estimatedCost };
  }, [draft.text, activeModel]);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1rem', alignItems: 'start' }}>
      <div>
        <QueryForm 
          onSubmit={onSubmit} 
          onResults={onResults} 
          isLoading={isLoading}
          onDraftChange={(d) => setDraft(d)}
          initialDraft={initial}
        />
        <button onClick={() => { clearDraft(); setDraft({ text: '', engines: ['openai'], intent: 'commercial', temperature: 0.2 }); }} style={{ marginTop: '0.5rem' }}>
          Reset draft
        </button>
      </div>
      <aside style={{ border: '1px solid #ddd', padding: '0.75rem', borderRadius: 8 }}>
        <h3 style={{ marginTop: 0 }}>Live Cost Estimate</h3>
        <div style={{ fontSize: 14 }}>
          <div><strong>Engine</strong>: {draft.engines?.includes('perplexity') ? 'perplexity' : 'openai'}</div>
          <div><strong>Model</strong>: {activeModel.id}</div>
          <div><strong>Input tokens</strong>: {estimate.inputTokens}</div>
          <div><strong>Input cost/1K</strong>: ${Number(activeModel.input_per_1k).toFixed(4)}</div>
          <hr />
          <div style={{ fontSize: 16 }}>
            <strong>Estimated cost</strong>: ${estimate.estimatedCost.toFixed(6)}
          </div>
          <p style={{ color: '#666', marginTop: '0.5rem' }}>Output tokens are not estimated. Actual cost is shown after submission.</p>
        </div>
      </aside>
    </div>
  );
}

export default QueryPage;


