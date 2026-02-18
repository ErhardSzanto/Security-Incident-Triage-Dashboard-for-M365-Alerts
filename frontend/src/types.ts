// API Types

export type Severity = 'low' | 'medium' | 'high' | 'critical';
export type IncidentStatus = 'new' | 'investigating' | 'contained' | 'closed';

export interface Alert {
  id: number;
  alert_id: string;
  source: string;
  category: string;
  severity: Severity;
  title: string;
  description: string | null;
  entity_user: string | null;
  entity_ip: string | null;
  entity_device: string | null;
  entity_location: string | null;
  timestamp: string;
  created_at: string;
}

export interface IncidentListItem {
  id: number;
  title: string;
  status: IncidentStatus;
  priority_score: number;
  alert_count: number;
  created_at: string;
  updated_at: string;
}

export interface ScoreExplanation {
  severity_score: number;
  severity_reason: string;
  entity_frequency_score: number;
  entity_reason: string;
  risk_indicator_score: number;
  risk_reasons: string[];
  total_score: number;
  alert_count: number;
}

export interface Incident {
  id: number;
  title: string;
  status: IncidentStatus;
  priority_score: number;
  score_explanation: string | null;
  related_users: string | null;
  related_ips: string | null;
  related_devices: string | null;
  related_locations: string | null;
  notes: string | null;
  evidence: string | null;
  created_at: string;
  updated_at: string;
  alerts: Alert[];
}

export interface DashboardStats {
  total_alerts: number;
  total_incidents: number;
  critical_incidents: number;
  new_incidents: number;
  investigating_incidents: number;
  contained_incidents: number;
  closed_incidents: number;
}

export interface UploadResponse {
  success: boolean;
  alerts_imported: number;
  incidents_created: number;
  message: string;
}

export interface IncidentUpdate {
  status?: IncidentStatus;
  notes?: string;
  evidence?: string;
}
