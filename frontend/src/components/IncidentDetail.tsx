import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api';
import type { Incident, IncidentStatus, ScoreExplanation } from '../types';

function getPriorityClass(score: number): string {
  if (score >= 70) return 'priority-critical';
  if (score >= 50) return 'priority-high';
  if (score >= 30) return 'priority-medium';
  return 'priority-low';
}

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [notes, setNotes] = useState('');
  const [evidence, setEvidence] = useState('');
  const [showReport, setShowReport] = useState(false);
  const [reportContent, setReportContent] = useState('');
  const [reportLoading, setReportLoading] = useState(false);

  useEffect(() => {
    async function fetchIncident() {
      if (!id) return;
      try {
        const data = await api.getIncident(Number(id));
        setIncident(data);
        setNotes(data.notes || '');
        setEvidence(data.evidence || '');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load incident');
      } finally {
        setLoading(false);
      }
    }
    fetchIncident();
  }, [id]);

  async function handleStatusChange(newStatus: IncidentStatus) {
    if (!incident) return;
    setSaving(true);
    try {
      const updated = await api.updateIncident(incident.id, { status: newStatus });
      setIncident(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update status');
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveNotes() {
    if (!incident) return;
    setSaving(true);
    try {
      const updated = await api.updateIncident(incident.id, { notes, evidence });
      setIncident(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save notes');
    } finally {
      setSaving(false);
    }
  }

  async function handleGenerateReport() {
    if (!incident) return;
    setReportLoading(true);
    try {
      const report = await api.getIncidentReport(incident.id);
      setReportContent(report);
      setShowReport(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate report');
    } finally {
      setReportLoading(false);
    }
  }

  function downloadReport() {
    const blob = new Blob([reportContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `incident-${incident?.id}-report.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        Loading incident...
      </div>
    );
  }

  if (error) {
    return <div className="message message-error">{error}</div>;
  }

  if (!incident) {
    return <div className="message message-error">Incident not found</div>;
  }

  const scoreExplanation: ScoreExplanation | null = incident.score_explanation 
    ? JSON.parse(incident.score_explanation) 
    : null;
  
  const relatedUsers: string[] = incident.related_users ? JSON.parse(incident.related_users) : [];
  const relatedIps: string[] = incident.related_ips ? JSON.parse(incident.related_ips) : [];
  const relatedDevices: string[] = incident.related_devices ? JSON.parse(incident.related_devices) : [];
  const relatedLocations: string[] = incident.related_locations ? JSON.parse(incident.related_locations) : [];

  const sortedAlerts = [...incident.alerts].sort((a, b) => 
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  return (
    <div>
      <Link to="/incidents" style={{ color: 'var(--text-secondary)', marginBottom: '1rem', display: 'inline-block' }}>
        ← Back to Incidents
      </Link>

      {/* Header */}
      <div className="incident-header">
        <div>
          <h1 className="incident-title">{incident.title}</h1>
          <div className="incident-meta">
            <span>ID: {incident.id}</span>
            <span>Created: {new Date(incident.created_at).toLocaleString()}</span>
            <span>Updated: {new Date(incident.updated_at).toLocaleString()}</span>
          </div>
        </div>
        <div className="incident-actions">
          <button 
            className="btn btn-secondary" 
            onClick={handleGenerateReport}
            disabled={reportLoading}
          >
            {reportLoading ? 'Generating...' : '📄 Export Report'}
          </button>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Priority Score */}
        <div className="card">
          <h3 className="card-title">Priority Score</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
            <span 
              className={`priority-score ${getPriorityClass(incident.priority_score)}`}
              style={{ width: '4rem', height: '4rem', fontSize: '1.25rem' }}
            >
              {Math.round(incident.priority_score)}
            </span>
            <span className={`status-badge status-${incident.status}`} style={{ fontSize: '0.875rem' }}>
              {incident.status}
            </span>
          </div>
          
          {scoreExplanation && (
            <div className="score-breakdown">
              <div className="score-item">
                <span className="score-label">Severity</span>
                <span className="score-value">{scoreExplanation.severity_score}</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '-0.5rem', marginBottom: '0.5rem' }}>
                {scoreExplanation.severity_reason}
              </div>
              <div className="score-item">
                <span className="score-label">Entity Frequency</span>
                <span className="score-value">{scoreExplanation.entity_frequency_score}</span>
              </div>
              <div className="score-item">
                <span className="score-label">Risk Indicators</span>
                <span className="score-value">{scoreExplanation.risk_indicator_score}</span>
              </div>
              {scoreExplanation.risk_reasons.length > 0 && (
                <ul style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', paddingLeft: '1rem' }}>
                  {scoreExplanation.risk_reasons.map((reason, i) => (
                    <li key={i}>{reason}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        {/* Status Workflow */}
        <div className="card">
          <h3 className="card-title">Status Workflow</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {(['new', 'investigating', 'contained', 'closed'] as IncidentStatus[]).map(status => (
              <button
                key={status}
                className={`btn ${incident.status === status ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => handleStatusChange(status)}
                disabled={saving || incident.status === status}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Related Entities */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 className="card-title">Related Entities</h3>
        <div className="grid-2">
          <div>
            <h4 style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              👤 Users ({relatedUsers.length})
            </h4>
            <div className="entity-list">
              {relatedUsers.length > 0 
                ? relatedUsers.map((u, i) => <span key={i} className="entity-tag">{u}</span>)
                : <span style={{ color: 'var(--text-secondary)' }}>None</span>
              }
            </div>
          </div>
          <div>
            <h4 style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              🌐 IP Addresses ({relatedIps.length})
            </h4>
            <div className="entity-list">
              {relatedIps.length > 0 
                ? relatedIps.map((ip, i) => <span key={i} className="entity-tag">{ip}</span>)
                : <span style={{ color: 'var(--text-secondary)' }}>None</span>
              }
            </div>
          </div>
          <div>
            <h4 style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              💻 Devices ({relatedDevices.length})
            </h4>
            <div className="entity-list">
              {relatedDevices.length > 0 
                ? relatedDevices.map((d, i) => <span key={i} className="entity-tag">{d}</span>)
                : <span style={{ color: 'var(--text-secondary)' }}>None</span>
              }
            </div>
          </div>
          <div>
            <h4 style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              📍 Locations ({relatedLocations.length})
            </h4>
            <div className="entity-list">
              {relatedLocations.length > 0 
                ? relatedLocations.map((l, i) => <span key={i} className="entity-tag">{l}</span>)
                : <span style={{ color: 'var(--text-secondary)' }}>None</span>
              }
            </div>
          </div>
        </div>
      </div>

      {/* Alert Timeline */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 className="card-title">Alert Timeline ({incident.alerts.length} alerts)</h3>
        <div className="timeline">
          {sortedAlerts.map(alert => (
            <div 
              key={alert.id} 
              className="timeline-item"
              style={{ borderLeftColor: `var(--severity-${alert.severity})` }}
            >
              <div className="timeline-time">
                {new Date(alert.timestamp).toLocaleString()}
              </div>
              <div className="timeline-content">
                <div className="timeline-title">{alert.title}</div>
                <div className="timeline-meta">
                  <span className={`severity-badge severity-${alert.severity}`} style={{ marginRight: '0.5rem' }}>
                    {alert.severity}
                  </span>
                  {alert.source} • {alert.category}
                </div>
                {alert.description && (
                  <p style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                    {alert.description}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Notes & Evidence */}
      <div className="grid-2">
        <div className="card">
          <h3 className="card-title">Analyst Notes</h3>
          <textarea
            className="form-textarea"
            placeholder="Add investigation notes..."
            value={notes}
            onChange={e => setNotes(e.target.value)}
          />
        </div>
        <div className="card">
          <h3 className="card-title">Evidence</h3>
          <textarea
            className="form-textarea"
            placeholder="Document evidence and findings..."
            value={evidence}
            onChange={e => setEvidence(e.target.value)}
          />
        </div>
      </div>
      <div style={{ marginTop: '1rem' }}>
        <button 
          className="btn btn-primary" 
          onClick={handleSaveNotes}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Notes & Evidence'}
        </button>
      </div>

      {/* Report Modal */}
      {showReport && (
        <div className="modal-overlay" onClick={() => setShowReport(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Incident Report</h3>
              <button className="modal-close" onClick={() => setShowReport(false)}>×</button>
            </div>
            <div className="modal-body">
              <pre className="report-preview">{reportContent}</pre>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowReport(false)}>
                Close
              </button>
              <button className="btn btn-primary" onClick={downloadReport}>
                Download .md
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
