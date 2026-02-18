import { useState, useEffect } from 'react';
import { api } from '../api';
import type { Alert } from '../types';

export default function AlertList() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [sourceFilter, setSourceFilter] = useState<string>('');

  useEffect(() => {
    async function fetchAlerts() {
      setLoading(true);
      try {
        const params: { severity?: string; source?: string } = {};
        if (severityFilter) params.severity = severityFilter;
        if (sourceFilter) params.source = sourceFilter;
        
        const data = await api.getAlerts(params);
        setAlerts(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load alerts');
      } finally {
        setLoading(false);
      }
    }
    fetchAlerts();
  }, [severityFilter, sourceFilter]);

  // Get unique sources for filter dropdown
  const sources = [...new Set(alerts.map(a => a.source))];

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Alerts</h1>
        <p className="page-subtitle">All ingested security alerts</p>
      </div>

      {/* Filters */}
      <div className="filters">
        <div className="filter-group">
          <label className="form-label" style={{ marginBottom: 0 }}>Severity:</label>
          <select 
            className="form-select" 
            style={{ width: 'auto' }}
            value={severityFilter}
            onChange={e => setSeverityFilter(e.target.value)}
          >
            <option value="">All</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        <div className="filter-group">
          <label className="form-label" style={{ marginBottom: 0 }}>Source:</label>
          <input
            type="text"
            className="form-input"
            style={{ width: '200px' }}
            placeholder="Filter by source..."
            value={sourceFilter}
            onChange={e => setSourceFilter(e.target.value)}
          />
        </div>
      </div>

      {error && <div className="message message-error">{error}</div>}

      {loading ? (
        <div className="loading">
          <div className="spinner" />
          Loading alerts...
        </div>
      ) : alerts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🔔</div>
          <p>No alerts found</p>
          <p style={{ fontSize: '0.875rem' }}>Upload JSON or CSV files to import alerts</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Title</th>
                  <th>Source</th>
                  <th>Category</th>
                  <th>User</th>
                  <th>IP</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map(alert => (
                  <tr key={alert.id}>
                    <td>
                      <span className={`severity-badge severity-${alert.severity}`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td style={{ maxWidth: '300px' }}>
                      <div style={{ fontWeight: 500 }}>{alert.title}</div>
                      {alert.description && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                          {alert.description.substring(0, 100)}
                          {alert.description.length > 100 && '...'}
                        </div>
                      )}
                    </td>
                    <td>{alert.source}</td>
                    <td>{alert.category}</td>
                    <td>
                      <span className="entity-tag" style={{ fontSize: '0.75rem' }}>
                        {alert.entity_user || '-'}
                      </span>
                    </td>
                    <td>
                      <span className="entity-tag" style={{ fontSize: '0.75rem' }}>
                        {alert.entity_ip || '-'}
                      </span>
                    </td>
                    <td style={{ whiteSpace: 'nowrap' }}>
                      {new Date(alert.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
