import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import type { IncidentListItem, IncidentStatus } from '../types';

function getPriorityClass(score: number): string {
  if (score >= 70) return 'priority-critical';
  if (score >= 50) return 'priority-high';
  if (score >= 30) return 'priority-medium';
  return 'priority-low';
}

export default function IncidentList() {
  const [incidents, setIncidents] = useState<IncidentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [minPriority, setMinPriority] = useState<string>('');

  useEffect(() => {
    async function fetchIncidents() {
      setLoading(true);
      try {
        const params: { status?: string; min_priority?: number } = {};
        if (statusFilter) params.status = statusFilter;
        if (minPriority) params.min_priority = Number(minPriority);
        
        const data = await api.getIncidents(params);
        setIncidents(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load incidents');
      } finally {
        setLoading(false);
      }
    }
    fetchIncidents();
  }, [statusFilter, minPriority]);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Incidents</h1>
        <p className="page-subtitle">Correlated security incidents requiring investigation</p>
      </div>

      {/* Filters */}
      <div className="filters">
        <div className="filter-group">
          <label className="form-label" style={{ marginBottom: 0 }}>Status:</label>
          <select 
            className="form-select" 
            style={{ width: 'auto' }}
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
          >
            <option value="">All</option>
            <option value="new">New</option>
            <option value="investigating">Investigating</option>
            <option value="contained">Contained</option>
            <option value="closed">Closed</option>
          </select>
        </div>
        <div className="filter-group">
          <label className="form-label" style={{ marginBottom: 0 }}>Min Priority:</label>
          <select 
            className="form-select" 
            style={{ width: 'auto' }}
            value={minPriority}
            onChange={e => setMinPriority(e.target.value)}
          >
            <option value="">Any</option>
            <option value="70">Critical (70+)</option>
            <option value="50">High (50+)</option>
            <option value="30">Medium (30+)</option>
          </select>
        </div>
      </div>

      {error && <div className="message message-error">{error}</div>}

      {loading ? (
        <div className="loading">
          <div className="spinner" />
          Loading incidents...
        </div>
      ) : incidents.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <p>No incidents found</p>
          <p style={{ fontSize: '0.875rem' }}>Upload alert data to generate incidents</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Priority</th>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Alerts</th>
                  <th>Created</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map(incident => (
                  <tr key={incident.id} className="clickable-row">
                    <td>
                      <span className={`priority-score ${getPriorityClass(incident.priority_score)}`}>
                        {Math.round(incident.priority_score)}
                      </span>
                    </td>
                    <td>
                      <Link 
                        to={`/incidents/${incident.id}`} 
                        style={{ color: 'inherit', textDecoration: 'none', fontWeight: 500 }}
                      >
                        {incident.title}
                      </Link>
                    </td>
                    <td>
                      <span className={`status-badge status-${incident.status}`}>
                        {incident.status}
                      </span>
                    </td>
                    <td>{incident.alert_count}</td>
                    <td>{new Date(incident.created_at).toLocaleString()}</td>
                    <td>{new Date(incident.updated_at).toLocaleString()}</td>
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
