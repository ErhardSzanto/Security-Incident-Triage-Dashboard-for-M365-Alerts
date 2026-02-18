import type { DashboardStats, IncidentListItem, Incident, Alert, UploadResponse, IncidentUpdate } from './types';

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'Request failed');
  }
  return response.json();
}

export const api = {
  // Dashboard
  getStats: () => fetchJson<DashboardStats>(`${API_BASE}/stats`),
  
  // Incidents
  getIncidents: (params?: { status?: string; min_priority?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.min_priority) searchParams.set('min_priority', String(params.min_priority));
    const query = searchParams.toString();
    return fetchJson<IncidentListItem[]>(`${API_BASE}/incidents${query ? `?${query}` : ''}`);
  },
  
  getHighPriorityIncidents: (limit = 10) => 
    fetchJson<IncidentListItem[]>(`${API_BASE}/incidents/high-priority?limit=${limit}`),
  
  getIncident: (id: number) => fetchJson<Incident>(`${API_BASE}/incidents/${id}`),
  
  updateIncident: (id: number, update: IncidentUpdate) => 
    fetchJson<Incident>(`${API_BASE}/incidents/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(update),
    }),
  
  getIncidentReport: async (id: number): Promise<string> => {
    const response = await fetch(`${API_BASE}/incidents/${id}/report`);
    if (!response.ok) throw new Error('Failed to generate report');
    return response.text();
  },
  
  // Alerts
  getAlerts: (params?: { severity?: string; source?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.severity) searchParams.set('severity', params.severity);
    if (params?.source) searchParams.set('source', params.source);
    const query = searchParams.toString();
    return fetchJson<Alert[]>(`${API_BASE}/alerts${query ? `?${query}` : ''}`);
  },
  
  getAlert: (id: number) => fetchJson<Alert>(`${API_BASE}/alerts/${id}`),
  
  // Data ingestion
  uploadFile: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || 'Upload failed');
    }
    return response.json();
  },
  
  seedDemoData: () => fetchJson<UploadResponse>(`${API_BASE}/seed`, { method: 'POST' }),
  
  recorrelate: () => fetchJson<UploadResponse>(`${API_BASE}/recorrelate`, { method: 'POST' }),
};
