import axios from 'axios';

export const API_BASE_URL = 'http://127.0.0.1:8000';

export const runQuery = async (queryData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/query/run`, queryData);
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw new Error('Failed to run query. Please try again.');
  }
};

export const streamQuery = ({ query, model, intent = 'unlabeled', temperature = 0.2 }) => {
  const url = new URL(`${API_BASE_URL}/query/stream`);
  url.searchParams.set('query', query);
  if (model) url.searchParams.set('model', model);
  if (intent) url.searchParams.set('intent', intent);
  url.searchParams.set('temperature', String(temperature));
  return new EventSource(url.toString());
};

export const getHealth = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/healthz`);
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    return { ok: false };
  }
};

export const getPricingModels = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/pricing/models`);
    return response.data;
  } catch (error) {
    console.error('Pricing fetch failed:', error);
    return { models: [], defaults: { input_per_1k: 0.0025, output_per_1k: 0.01 } };
  }
};

export const getCostsStats = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/stats/costs`);
    return response.data;
  } catch (error) {
    console.error('Costs stats fetch failed:', error);
    return { total_cost_usd: 0, total_runs: 0, by_engine: {}, by_model: {} };
  }
};

export const listRuns = async (limit = 50, offset = 0) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/runs`, { params: { limit, offset } });
    return response.data;
  } catch (error) {
    console.error('List runs failed:', error);
    return { items: [], limit, offset };
  }
};

export const getRun = async (runId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/runs/${encodeURIComponent(runId)}`);
    return response.data;
  } catch (error) {
    console.error('Get run failed:', error);
    throw error;
  }
};

export const lookupRuns = async ({ query, engines }) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/runs/lookup`, { query, engines });
    return response.data;
  } catch (error) {
    console.error('Lookup runs failed:', error);
    return { matches: [] };
  }
};

export const deleteRun = async (runId) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/runs/${encodeURIComponent(runId)}`);
    return response.data;
  } catch (error) {
    console.error('Delete run failed:', error);
    throw error;
  }
};

