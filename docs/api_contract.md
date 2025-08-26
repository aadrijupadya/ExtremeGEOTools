# ExtremeGEOTools - API Contract

## 🌐 **API Overview**

The ExtremeGEOTools API provides endpoints for query execution, metrics retrieval, and automation control. All endpoints return JSON responses and use standard HTTP status codes.

**Base URL**: `http://localhost:8000` (development)

## 🔐 **Authentication**

Currently, the API uses **API keys** for external AI services:
- `OPENAI_API_KEY` - For OpenAI endpoints
- `PERPLEXITY_API_KEY` - For Perplexity endpoints

## 📊 **Query Execution Endpoints**

### **POST /query**

Execute a query against specified AI engines.

**Request Body:**
```json
{
  "query": "string",
  "engines": ["openai", "perplexity"],
  "intent": "string",
  "prompt_version": "string",
  "temperature": 0.2
}
```

**Response:**
```json
{
  "runs": [
    {
      "id": "string",
      "ts": "ISO timestamp",
      "query": "string",
      "engine": "string",
      "model": "string",
      "status": "ok|error",
      "latency_ms": 1234,
      "input_tokens": 100,
      "output_tokens": 500,
      "cost_usd": 0.0025,
      "raw_excerpt": "string",
      "vendors": [...],
      "links": [...],
      "domains": [...],
      "extreme_mentioned": true,
      "extreme_rank": 3
    }
  ]
}
```

### **GET /query/stream**

Stream query execution in real-time using Server-Sent Events (SSE).

**Query Parameters:**
- `query` (required): Search query
- `engine` (optional): AI engine to use
- `model` (optional): Specific model
- `intent` (optional): Query intent
- `temperature` (optional): Response creativity (0.0-1.0)

**SSE Events:**
- `start`: Query execution started
- `delta`: Text chunk received
- `done`: Query completed
- `error`: Error occurred

## 📈 **Metrics Endpoints**

### **GET /metrics/enhanced-analysis**

Get comprehensive citation and competitor analysis.

**Query Parameters:**
- `days` (default: 7): Number of days to analyze
- `engine` (optional): Filter by engine

**Response:**
```json
{
  "period_days": 7,
  "start_date": "2024-01-01",
  "end_date": "2024-01-08",
  "total_runs_analyzed": 150,
  "run_source": "automated",
  "analysis": {
    "citations": {
      "total_citations": 450,
      "unique_domains": 89,
      "avg_domain_quality": 7.2,
      "top_5_websites_by_mentions": [...],
      "quality_distribution": {
        "excellent": 45,
        "good": 120,
        "fair": 200,
        "poor": 85
      }
    },
    "competitors": {
      "total_entity_mentions": 234,
      "unique_entities": 12,
      "top_competitors": [...],
      "extreme_networks_detection_rate": 0.85,
      "extreme_networks_detailed_analysis": {...}
    }
  }
}
```

### **GET /metrics/query-overview**

Get overview of recent queries and performance metrics.

**Query Parameters:**
- `days` (default: 7): Number of days to analyze
- `engine` (optional): Filter by engine

**Response:**
```json
{
  "period_days": 7,
  "start_date": "2024-01-01",
  "end_date": "2024-01-08",
  "total_runs": 150,
  "successful_runs": 142,
  "failed_runs": 8,
  "total_cost_usd": 12.45,
  "avg_cost_per_query": 0.083,
  "engine_breakdown": {
    "openai": {"runs": 75, "cost": 6.23},
    "perplexity": {"runs": 75, "cost": 6.22}
  }
}
```

### **GET /metrics/competitor-analysis**

Get detailed competitor analysis and market positioning.

**Query Parameters:**
- `days` (default: 7): Number of days to analyze
- `engine` (optional): Filter by engine

**Response:**
```json
{
  "period_days": 7,
  "start_date": "2024-01-01",
  "end_date": "2024-01-08",
  "competitor_insights": {
    "total_competitors": 12,
    "top_competitors": [
      {
        "name": "Cisco",
        "mentions": 45,
        "avg_rank": 2.3,
        "share_of_voice": 0.28
      }
    ],
    "extreme_networks_positioning": {
      "total_mentions": 38,
      "avg_rank": 4.1,
      "detection_rate": 0.85
    }
  }
}
```

## 📋 **Run History Endpoints**

### **GET /runs**

Get paginated list of query runs.

**Query Parameters:**
- `limit` (default: 50): Number of runs to return
- `offset` (default: 0): Pagination offset
- `engine` (optional): Filter by engine
- `status` (optional): Filter by status
- `days` (optional): Filter by recent days

**Response:**
```json
{
  "items": [
    {
      "id": "string",
      "ts": "ISO timestamp",
      "query": "string",
      "engine": "string",
      "model": "string",
      "prompt_version": "string",
      "intent": "string",
      "is_branded": true,
      "status": "string",
      "latency_ms": 1234,
      "input_tokens": 100,
      "output_tokens": 500,
      "cost_usd": 0.0025,
      "preview": "..."
    }
  ],
  "limit": 50,
  "offset": 0
}
```

### **GET /runs/{id}**

Get detailed information about a specific run.

**Response:**
```json
{
  "id": "string",
  "ts": "ISO timestamp",
  "query": "string",
  "engine": "string",
  "model": "string",
  "prompt_version": "string",
  "intent": "string",
  "is_branded": true,
  "status": "string",
  "latency_ms": 1234,
  "input_tokens": 100,
  "output_tokens": 500,
  "cost_usd": 0.0025,
  "raw_excerpt": "string",
  "vendors": [...],
  "links": [...],
  "domains": [...],
  "citations_enriched": [...],
  "entities_normalized": [...],
  "extreme_mentioned": true,
  "extreme_rank": 3
}
```

## ⚙️ **Automation Endpoints**

### **POST /scheduler/compute-metrics**

Manually trigger metrics computation for a specific date.

**Request Body:**
```json
{
  "target_date": "2024-01-01",
  "engine": "openai"
}
```

**Response:**
```json
{
  "date": "2024-01-01",
  "engine": "openai",
  "message": "Successfully computed 3 metrics",
  "metrics_computed": 3,
  "contexts": ["extreme_networks", "competitors"]
}
```

### **GET /scheduler/status**

Get current automation status and schedule information.

**Response:**
```json
{
  "automation_enabled": true,
  "last_run": "2024-01-08T10:00:00Z",
  "next_scheduled_run": "2024-01-09T10:00:00Z",
  "total_scheduled_queries": 25,
  "success_rate": 0.96
}
```

## 📊 **Statistics Endpoints**

### **GET /stats/costs**

Get cost breakdown and statistics.

**Query Parameters:**
- `start` (optional): Start date filter
- `end` (optional): End date filter

**Response:**
```json
{
  "total_cost_usd": 45.67,
  "total_runs": 1500,
  "by_engine": {
    "openai": {"cost": 23.45, "runs": 750},
    "perplexity": {"cost": 22.22, "runs": 750}
  },
  "by_model": {
    "gpt-4o-mini": {"cost": 15.67, "runs": 500},
    "sonar": {"cost": 22.22, "runs": 750}
  }
}
```

## 🔧 **Utility Endpoints**

### **GET /health**

Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-08T10:00:00Z",
  "version": "1.0.0",
  "database": "connected",
  "external_apis": {
    "openai": "available",
    "perplexity": "available"
  }
}
```

## 📝 **Error Handling**

All endpoints return consistent error responses:

**Error Response Format:**
```json
{
  "detail": "Error message description",
  "error_code": "ERROR_TYPE",
  "timestamp": "2024-01-08T10:00:00Z"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## 🚀 **Rate Limiting**

- **Query endpoints**: 10 requests per minute per IP
- **Metrics endpoints**: 60 requests per minute per IP
- **Streaming endpoints**: 5 concurrent connections per IP

## 📚 **Usage Examples**

### **Python Client Example**
```python
import requests

# Execute a query
response = requests.post("http://localhost:8000/query", json={
    "query": "What are the top enterprise networking vendors?",
    "engines": ["openai"],
    "intent": "competitive_analysis"
})

# Get metrics
metrics = requests.get("http://localhost:8000/metrics/enhanced-analysis?days=7&engine=openai")
```

### **JavaScript Client Example**
```javascript
// Execute a query
const response = await fetch('/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        query: 'What are the top enterprise networking vendors?',
        engines: ['openai'],
        intent: 'competitive_analysis'
    })
});

// Get metrics
const metrics = await fetch('/metrics/enhanced-analysis?days=7&engine=openai');
```

## 🔄 **WebSocket/SSE Support**

The `/query/stream` endpoint supports Server-Sent Events for real-time query execution:

```javascript
const eventSource = new EventSource('/query/stream?query=test&engine=openai');

eventSource.addEventListener('start', (event) => {
    const data = JSON.parse(event.data);
    console.log('Query started:', data.run_id);
});

eventSource.addEventListener('delta', (event) => {
    const data = JSON.parse(event.data);
    console.log('Text chunk:', data.text);
});

eventSource.addEventListener('done', (event) => {
    console.log('Query completed');
    eventSource.close();
});
```

