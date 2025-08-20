import React, { useState, useEffect } from 'react';
import { triggerDailyQueries, getSchedulerConfig, getSchedulerStatus } from '../services/api';

function Scheduler() {
  const [config, setConfig] = useState(null);
  const [status, setStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSchedulerInfo();
  }, []);

  const loadSchedulerInfo = async () => {
    try {
      const [configData, statusData] = await Promise.all([
        getSchedulerConfig(),
        getSchedulerStatus()
      ]);
      setConfig(configData);
      setStatus(statusData);
    } catch (err) {
      setError('Failed to load scheduler information');
      console.error('Error loading scheduler info:', err);
    }
  };

  const handleExecuteQueries = async (dryRun = true, limit = null) => {
    setIsLoading(true);
    setError(null);
    setExecutionResult(null);

    try {
      const result = await triggerDailyQueries({
        dry_run: dryRun,
        limit: limit
      });
      
      setExecutionResult(result);
      
      // Reload status after execution
      if (!dryRun) {
        setTimeout(loadSchedulerInfo, 1000);
      }
    } catch (err) {
      setError('Failed to execute queries');
      console.error('Error executing queries:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (timeStr) => {
    if (!timeStr) return 'N/A';
    return timeStr;
  };

  if (error) {
    return (
      <div className="scheduler error">
        <h3>Query Scheduler</h3>
        <div className="error-message">{error}</div>
        <button onClick={loadSchedulerInfo} className="retry-btn">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="scheduler">
      <h3>Query Scheduler</h3>
      
      {config && (
        <div className="scheduler-config">
          <h4>Configuration</h4>
          <div className="config-grid">
            <div className="config-item">
              <span className="label">Schedule:</span>
              <span className="value">{config.cadence} at {formatTime(config.morning_time)}</span>
            </div>
            <div className="config-item">
              <span className="label">Total Queries/Day:</span>
              <span className="value">{config.total_queries_per_day}</span>
            </div>
            <div className="config-item">
              <span className="label">Engine Distribution:</span>
              <span className="value">
                {Object.entries(config.engine_distribution).map(([engine, count]) => 
                  `${engine}: ${count}`
                ).join(', ')}
              </span>
            </div>
            <div className="config-item">
              <span className="label">Competitors:</span>
              <span className="value">{config.competitor_set.join(', ')}</span>
            </div>
          </div>
        </div>
      )}

      {status && (
        <div className="scheduler-status">
          <h4>Today's Status</h4>
          <div className="status-grid">
            <div className="status-item">
              <span className="label">Date:</span>
              <span className="value">{status.date}</span>
            </div>
            <div className="status-item">
              <span className="label">Scheduled:</span>
              <span className="value">{status.total_queries_scheduled}</span>
            </div>
            <div className="status-item">
              <span className="label">Executed:</span>
              <span className="value">{status.queries_executed_today}</span>
            </div>
            <div className="status-item">
              <span className="label">Remaining:</span>
              <span className="value">{status.queries_remaining}</span>
            </div>
            <div className="status-item">
              <span className="label">Next Run:</span>
              <span className="value">{formatTime(status.next_run_time)}</span>
            </div>
            <div className="status-item">
              <span className="label">Status:</span>
              <span className={`value status-${status.status}`}>{status.status}</span>
            </div>
          </div>
        </div>
      )}

      <div className="scheduler-controls">
        <h4>Execute Queries</h4>
        <div className="control-buttons">
          <button
            onClick={() => handleExecuteQueries(true)}
            disabled={isLoading}
            className="btn btn-secondary"
          >
            {isLoading ? 'Loading...' : 'Dry Run (All)'}
          </button>
          
          <button
            onClick={() => handleExecuteQueries(true, 5)}
            disabled={isLoading}
            className="btn btn-secondary"
          >
            {isLoading ? 'Loading...' : 'Dry Run (5 queries)'}
          </button>
          
          <button
            onClick={() => handleExecuteQueries(false, 5)}
            disabled={isLoading}
            className="btn btn-primary"
          >
            {isLoading ? 'Executing...' : 'Execute (5 queries)'}
          </button>
          
          <button
            onClick={() => handleExecuteQueries(false)}
            disabled={isLoading}
            className="btn btn-danger"
          >
            {isLoading ? 'Executing...' : 'Execute All'}
          </button>
        </div>
      </div>

      {executionResult && (
        <div className="execution-result">
          <h4>Execution Result</h4>
          <div className="result-grid">
            <div className="result-item">
              <span className="label">Date:</span>
              <span className="value">{executionResult.target_date}</span>
            </div>
            <div className="result-item">
              <span className="label">Total Queries:</span>
              <span className="value">{executionResult.total_queries}</span>
            </div>
            <div className="result-item">
              <span className="label">Executed:</span>
              <span className="value">{executionResult.executed_queries}</span>
            </div>
            <div className="result-item">
              <span className="label">Execution Time:</span>
              <span className="value">{executionResult.execution_time}</span>
            </div>
            <div className="result-item">
              <span className="label">Mode:</span>
              <span className="value">{executionResult.dry_run ? 'Dry Run' : 'Live Execution'}</span>
            </div>
          </div>
          
          {executionResult.status_distribution && (
            <div className="status-breakdown">
              <h5>Status Breakdown</h5>
              <div className="status-list">
                {Object.entries(executionResult.status_distribution).map(([status, count]) => (
                  <div key={status} className="status-entry">
                    <span className="status-name">{status}:</span>
                    <span className="status-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <style jsx>{`
        .scheduler {
          background: white;
          border-radius: 8px;
          padding: 20px;
          margin: 20px 0;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .scheduler h3 {
          margin-top: 0;
          color: #333;
          border-bottom: 2px solid #007bff;
          padding-bottom: 10px;
        }

        .scheduler h4 {
          color: #555;
          margin: 20px 0 10px 0;
        }

        .config-grid, .status-grid, .result-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin-bottom: 20px;
        }

        .config-item, .status-item, .result-item {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }

        .label {
          font-weight: 600;
          color: #666;
          font-size: 0.9em;
        }

        .value {
          color: #333;
          font-size: 1em;
        }

        .status-active {
          color: #28a745;
          font-weight: 600;
        }

        .status-inactive {
          color: #dc3545;
          font-weight: 600;
        }

        .control-buttons {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          margin-top: 10px;
        }

        .btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          transition: background-color 0.2s;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-primary {
          background-color: #007bff;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background-color: #0056b3;
        }

        .btn-secondary {
          background-color: #6c757d;
          color: white;
        }

        .btn-secondary:hover:not(:disabled) {
          background-color: #545b62;
        }

        .btn-danger {
          background-color: #dc3545;
          color: white;
        }

        .btn-danger:hover:not(:disabled) {
          background-color: #c82333;
        }

        .execution-result {
          background-color: #f8f9fa;
          border-radius: 6px;
          padding: 15px;
          margin-top: 20px;
        }

        .status-breakdown {
          margin-top: 15px;
        }

        .status-list {
          display: flex;
          gap: 20px;
          flex-wrap: wrap;
        }

        .status-entry {
          display: flex;
          gap: 8px;
          align-items: center;
        }

        .status-name {
          font-weight: 600;
          color: #666;
        }

        .status-count {
          background-color: #007bff;
          color: white;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 0.9em;
        }

        .error {
          border: 1px solid #dc3545;
        }

        .error-message {
          color: #dc3545;
          margin: 10px 0;
        }

        .retry-btn {
          background-color: #dc3545;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 4px;
          cursor: pointer;
        }

        .retry-btn:hover {
          background-color: #c82333;
        }
      `}</style>
    </div>
  );
}

export default Scheduler;
