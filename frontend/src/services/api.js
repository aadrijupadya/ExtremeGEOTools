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

// Scheduler API functions
export const getSchedulerConfig = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/scheduler/config`);
    return response.data;
  } catch (error) {
    console.error('Scheduler config fetch failed:', error);
    throw error;
  }
};

export const getSchedulerStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/scheduler/status`);
    return response.data;
  } catch (error) {
    console.error('Scheduler status fetch failed:', error);
    throw error;
  }
};

export const triggerDailyQueries = async (requestData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/scheduler/execute`, requestData);
    return response.data;
  } catch (error) {
    console.error('Trigger daily queries failed:', error);
    throw error;
  }
};

// Enhanced Metrics Analysis
export const getEnhancedAnalysis = async (days = 7, engine = null) => {
  try {
    let url = `${API_BASE_URL}/metrics/enhanced-analysis?days=${days}`;
    if (engine) {
      url += `&engine=${engine}`;
    }
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching enhanced analysis:', error);
    throw error;
  }
};

// Recent Queries with Real Data
export const getRecentQueries = async (days = 7, engine = null, limit = 50) => {
  try {
    let url = `${API_BASE_URL}/metrics/recent-queries?days=${days}&limit=${limit}`;
    if (engine) {
      url += `&engine=${engine}`;
    }
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching recent queries:', error);
    throw error;
  }
};

// Extreme Focus Metrics
export const getExtremeFocusMetrics = async (startDate, endDate, engine = null) => {
  try {
    let url = `${API_BASE_URL}/metrics/extreme-focus?start_date=${startDate}&end_date=${endDate}`;
    if (engine) {
      url += `&engine=${engine}`;
    }
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching Extreme Focus metrics:', error);
    throw error;
  }
};

export const getCitationAnalysis = async (startDate, endDate, engine = null) => {
  try {
    let url = `${API_BASE_URL}/metrics/citation-analysis?start_date=${startDate}&end_date=${endDate}`;
    if (engine) {
      url += `&engine=${engine}`;
    }
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching Citation Analysis:', error);
    throw error;
  }
};

// Entity Associations API functions
export const getEntityAssociations = async (engine = null) => {
  try {
    let url = `${API_BASE_URL}/entity-associations`;
    if (engine) {
      url += `?engine=${engine}`;
    }
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching entity associations:', error);
    throw error;
  }
};

export const getProductAssociations = async (engine = null) => {
  try {
    let url = `${API_BASE_URL}/entity-associations/products`;
    if (engine) {
      url += `?engine=${engine}`;
    }
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching product associations:', error);
    throw error;
  }
};

export const getKeywordAssociations = async (engine = null) => {
  try {
    let url = `${API_BASE_URL}/entity-associations/keywords`;
    if (engine) {
      url += `?engine=${engine}`;
    }
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching keyword associations:', error);
    throw error;
  }
};

