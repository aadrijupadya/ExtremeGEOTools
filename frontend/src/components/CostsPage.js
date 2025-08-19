import React, { useEffect, useMemo, useState } from 'react';
import BrandIcon from './BrandIcon';
import { getCostsStats, getPricingModels } from '../services/api';

function Currency({ value }) {
  return <span>${Number(value || 0).toFixed(6)}</span>;
}

function CostsPage() {
  const [stats, setStats] = useState({ total_cost_usd: 0, total_runs: 0, by_engine: {}, by_model: {} });
  const [pricing, setPricing] = useState({ models: [], defaults: { input_per_1k: 0.0025, output_per_1k: 0.01 } });

  // Explorer state
  const [engine, setEngine] = useState('openai');
  const [model, setModel] = useState('gpt-4o-search-preview');
  const [queriesPerDay, setQueriesPerDay] = useState(50);
  const [days, setDays] = useState(30);
  const [avgInTokens, setAvgInTokens] = useState(800);
  const [avgOutTokens, setAvgOutTokens] = useState(400);

  useEffect(() => {
    (async () => {
      const s = await getCostsStats();
      setStats(s || { total_cost_usd: 0, total_runs: 0, by_engine: {}, by_model: {} });
      const p = await getPricingModels();
      setPricing(p || { models: [], defaults: { input_per_1k: 0.0025, output_per_1k: 0.01 } });
    })();
  }, []);

  const modelPricing = useMemo(() => {
    const m = (pricing.models || []).find(x => x.id === model);
    return m || { id: model, input_per_1k: pricing.defaults?.input_per_1k || 0.0025, output_per_1k: pricing.defaults?.output_per_1k || 0.01 };
  }, [pricing, model]);

  const estimate = useMemo(() => {
    const q = Math.max(0, Number(queriesPerDay) || 0);
    const d = Math.max(1, Number(days) || 1);
    const inTok = Math.max(0, Number(avgInTokens) || 0);
    const outTok = Math.max(0, Number(avgOutTokens) || 0);
    const totalIn = q * d * inTok;
    const totalOut = q * d * outTok;
    const costIn = (totalIn / 1000) * (modelPricing.input_per_1k || 0);
    const costOut = (totalOut / 1000) * (modelPricing.output_per_1k || 0);
    const total = costIn + costOut;
    return { costIn, costOut, total, totalIn, totalOut };
  }, [queriesPerDay, days, avgInTokens, avgOutTokens, modelPricing]);

  const openAiModels = useMemo(() => [
    { id: 'gpt-4o-search-preview', label: 'gpt-4o-search-preview' },
    { id: 'gpt-5-mini', label: 'gpt-5-mini' },
  ], []);
  const pplxModels = useMemo(() => [
    { id: 'sonar', label: 'sonar' },
    { id: 'sonar-pro', label: 'sonar-pro' },
    { id: 'sonar-reasoning', label: 'sonar-reasoning' },
  ], []);

  useEffect(() => {
    if (engine === 'openai' && !openAiModels.find(m => m.id === model)) setModel('gpt-4o-search-preview');
    if (engine === 'perplexity' && !pplxModels.find(m => m.id === model)) setModel('sonar');
  }, [engine]);

  return (
    <div>
      <h2>Costs</h2>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <div className="card"><div className="card-body"><div className="kpi">{stats.total_runs.toLocaleString()}</div><div className="kpi-small">Total runs</div></div></div>
        <div className="card"><div className="card-body"><div className="kpi"><Currency value={stats.total_cost_usd} /></div><div className="kpi-small">Total cost</div></div></div>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-body">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, gap: 12, flexWrap: 'wrap' }}>
            <div>
              <h3 style={{ margin: 0 }}>Explore costs</h3>
              <div className="subtle">Estimate spend for different engines and models. Toggle options and tune assumptions.</div>
            </div>
            <div className="seg-group" role="tablist">
              <button className={`seg ${engine==='openai'?'seg-active':''}`} onClick={() => setEngine('openai')} role="tab">
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <BrandIcon name="chatgpt" size={14} /> OpenAI
                </span>
              </button>
              <button className={`seg ${engine==='perplexity'?'seg-active':''}`} onClick={() => setEngine('perplexity')} role="tab">
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <BrandIcon name="perplexity" size={14} /> Perplexity
                </span>
              </button>
            </div>
          </div>

          <div className="grid-2">
            <div className="grid">
              <div>
                <label style={{ display: 'block', fontWeight: 700, marginBottom: 4 }}>Model</label>
                <select value={model} onChange={(e) => setModel(e.target.value)} className="input">
                  {(engine === 'openai' ? openAiModels : pplxModels).map(m => (
                    <option key={m.id} value={m.id}>{m.label}</option>
                  ))}
                </select>
              </div>
              <div className="grid-2">
                <div>
                  <label style={{ display: 'block', fontWeight: 700, marginBottom: 4 }}>Queries/day</label>
                  <input type="number" value={queriesPerDay} onChange={(e) => setQueriesPerDay(e.target.value)} min={0} className="input" />
                </div>
                <div>
                  <label style={{ display: 'block', fontWeight: 700, marginBottom: 4 }}>Days</label>
                  <input type="number" value={days} onChange={(e) => setDays(e.target.value)} min={1} className="input" />
                </div>
              </div>
              <div className="grid-2">
                <div>
                  <label style={{ display: 'block', fontWeight: 700, marginBottom: 4 }}>Avg input tokens</label>
                  <input type="number" value={avgInTokens} onChange={(e) => setAvgInTokens(e.target.value)} min={0} className="input" />
                </div>
                <div>
                  <label style={{ display: 'block', fontWeight: 700, marginBottom: 4 }}>Avg output tokens</label>
                  <input type="number" value={avgOutTokens} onChange={(e) => setAvgOutTokens(e.target.value)} min={0} className="input" />
                </div>
              </div>
              <div className="subtle">Tip: Token counts are per query averages across your workload.</div>
            </div>

            <div className="card" style={{ alignSelf: 'stretch' }}>
              <div className="card-body" style={{ display: 'grid', gap: 8 }}>
                <div className="subtle">Pricing used</div>
                <div><strong>Input</strong>: ${Number(modelPricing.input_per_1k || 0).toFixed(4)} / 1K tokens</div>
                <div><strong>Output</strong>: ${Number(modelPricing.output_per_1k || 0).toFixed(4)} / 1K tokens</div>
                <hr className="rule" />
                <div><strong>Total input tokens</strong>: {estimate.totalIn.toLocaleString()}</div>
                <div><strong>Total output tokens</strong>: {estimate.totalOut.toLocaleString()}</div>
                <div><strong>Input cost</strong>: <Currency value={estimate.costIn} /></div>
                <div><strong>Output cost</strong>: <Currency value={estimate.costOut} /></div>
                <div className="kpi" style={{ marginTop: 6 }}>Estimated total: <Currency value={estimate.total} /></div>
                <div className="subtle">For {days} days at {queriesPerDay} queries/day</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-body">
            <h3 style={{ marginTop: 0 }}>By Engine</h3>
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
        </div>

        <div className="card">
          <div className="card-body">
            <h3 style={{ marginTop: 0 }}>By Model</h3>
            <table width="100%" cellPadding="6" style={{ borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th align="left">Model</th>
                  <th align="right">Runs</th>
                  <th align="right">Cost</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats.by_model || {}).map(([modelId, v]) => (
                  <tr key={modelId}>
                    <td>{modelId}</td>
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
    </div>
  );
}

export default CostsPage;


