import { useState, useRef } from 'react';
import { api } from '../api';
import type { UploadResponse } from '../types';

export default function DataUpload() {
  const [uploading, setUploading] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFileUpload(file: File) {
    setUploading(true);
    setMessage(null);
    try {
      const result = await api.uploadFile(file);
      setMessage({ type: 'success', text: result.message });
    } catch (err) {
      setMessage({ 
        type: 'error', 
        text: err instanceof Error ? err.message : 'Upload failed' 
      });
    } finally {
      setUploading(false);
    }
  }

  async function handleSeedDemo() {
    setSeeding(true);
    setMessage(null);
    try {
      const result = await api.seedDemoData();
      setMessage({ type: 'success', text: result.message });
    } catch (err) {
      setMessage({ 
        type: 'error', 
        text: err instanceof Error ? err.message : 'Failed to load demo data' 
      });
    } finally {
      setSeeding(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Upload Data</h1>
        <p className="page-subtitle">Import security alerts from JSON or CSV files</p>
      </div>

      {message && (
        <div className={`message message-${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="grid-2">
        {/* File Upload */}
        <div className="card">
          <h3 className="card-title">Upload Alert File</h3>
          <div
            className={`upload-area ${dragOver ? 'dragover' : ''}`}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="upload-icon">📁</div>
            <p className="upload-text">
              {uploading ? 'Uploading...' : 'Drag & drop or click to select'}
            </p>
            <p className="upload-hint">Supports JSON and CSV files</p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json,.csv"
            style={{ display: 'none' }}
            onChange={handleFileSelect}
          />
        </div>

        {/* Demo Data */}
        <div className="card">
          <h3 className="card-title">Demo Dataset</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
            Load sample security alerts to explore the dashboard functionality.
            This will import realistic M365 security alerts with various severities,
            categories, and entity relationships.
          </p>
          <button
            className="btn btn-primary"
            onClick={handleSeedDemo}
            disabled={seeding}
            style={{ width: '100%' }}
          >
            {seeding ? 'Loading...' : '🎲 Load Demo Dataset'}
          </button>
        </div>
      </div>

      {/* File Format Guide */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <h3 className="card-title">Supported Formats</h3>
        <div className="grid-2">
          <div>
            <h4 style={{ marginBottom: '0.5rem' }}>JSON Format</h4>
            <pre style={{ 
              backgroundColor: 'var(--bg-card)', 
              padding: '1rem', 
              borderRadius: 'var(--radius)',
              fontSize: '0.75rem',
              overflow: 'auto'
            }}>
{`[
  {
    "id": "alert-001",
    "title": "Suspicious Sign-in",
    "severity": "high",
    "category": "Identity",
    "user": "john@example.com",
    "ip": "192.168.1.1",
    "timestamp": "2024-01-15T10:30:00Z"
  }
]`}
            </pre>
          </div>
          <div>
            <h4 style={{ marginBottom: '0.5rem' }}>CSV Format</h4>
            <pre style={{ 
              backgroundColor: 'var(--bg-card)', 
              padding: '1rem', 
              borderRadius: 'var(--radius)',
              fontSize: '0.75rem',
              overflow: 'auto'
            }}>
{`id,title,severity,category,user,ip,timestamp
alert-001,Suspicious Sign-in,high,Identity,john@example.com,192.168.1.1,2024-01-15T10:30:00Z`}
            </pre>
          </div>
        </div>
        <p style={{ color: 'var(--text-secondary)', marginTop: '1rem', fontSize: '0.875rem' }}>
          The system automatically normalizes various field names (e.g., "userPrincipalName", "user", "account" → entity_user).
          Supported sources include Microsoft Defender, Azure AD, and generic alert formats.
        </p>
      </div>
    </div>
  );
}
