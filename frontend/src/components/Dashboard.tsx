import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import type { DashboardStats, IncidentListItem } from '../types';

function getPriorityClass(score: number): string {
  if (score >= 70) return 'priority-critical';
  if (score >= 50) return 'priority-high';
  if (score >= 30) return 'priority-medium';
  return 'priority-low';
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [highPriority, setHighPriority] = useState<IncidentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsData, priorityData] = await Promise.all([
          api.getStats(),
          api.getHighPriorityIncidents(10),
        ]);
        setStats(statsData);
        setHighPriority(priorityData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        Loading dashboard...
      </div>
    );
  }

  if (error) {
    return <div className="message message-error">{error}</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Security Dashboard</h1>
        <p className="page-subtitle">Overview of security incidents and alerts</p>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Alerts</div>
          <div className="stat-value">{stats?.total_alerts || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Incidents</div>
          <div className="stat-value">{stats?.total_incidents || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Critical Priority</div>
          <div className="stat-value critical">{stats?.critical_incidents || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">New</div>
          <div className="stat-value new">{stats?.new_incidents || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Investigating</div>
          <div className="stat-value investigating">{stats?.investigating_incidents || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Contained</div>
          <div className="stat-value">{stats?.contained_incidents || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Closed</div>
          <div className="stat-value">{stats?.closed_incidents || 0}</div>
        </div>
      </div>

      {/* High Priority Queue */}
      <div className="card">
        <h2 className="card-title">🔥 High Priority Queue</h2>
        {highPriority.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">✅</div>
            <p>No active high-priority incidents</p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Priority</th>
                  <th>Incident</th>
                  <th>Status</th>
                  <th>Alerts</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {highPriority.map(incident => (
                  <tr key={incident.id} className="clickable-row">
                    <td>
                      <span className={`priority-score ${getPriorityClass(incident.priority_score)}`}>
                        {Math.round(incident.priority_score)}
                      </span>
                    </td>
                    <td>
                      <Link to={`/incidents/${incident.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                        {incident.title}
                      </Link>
                    </td>
                    <td>
                      <span className={`status-badge status-${incident.status}`}>
                        {incident.status}
                      </span>
                    </td>
                    <td>{incident.alert_count}</td>
                    <td>{new Date(incident.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {highPriority.length > 0 && (
          <div style={{ marginTop: '1rem', textAlign: 'right' }}>
            <Link to="/incidents" className="btn btn-secondary">
              View All Incidents →
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
