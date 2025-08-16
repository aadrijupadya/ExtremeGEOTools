import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

export const runQuery = async (queryData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/query/run`, queryData);
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw new Error('Failed to run query. Please try again.');
  }
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

