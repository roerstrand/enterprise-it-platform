export type SlaState = 'on_track' | 'at_risk' | 'breached' | 'met';

// Alltid färskt beräknad server-side (server/domain/sla.py), aldrig lagrad direkt - se incident_server.py
export interface IncidentSla {
    response_deadline: string;
    resolution_deadline: string;
    first_response_at: string | null;
    resolved_at: string | null;
    response_breached: boolean;
    resolution_breached: boolean;
    state: SlaState;
    remaining_seconds: number;
}

export interface Incident {
    id: number;
    title: string;
    description: string;
    status: string;
    severity: string;
    ci_id: number;
    ai_summary: string;
    ai_summary_status: string;
    ai_suggested_severity: string;
    ai_suggested_status: string;
    created_at: string;
    updated_at: string;
    assignee_user_id: number | null;
    sla: IncidentSla;
}

// GET /demo/api/incidents/{id} - incidenten berikad med CI/ägar-info, för detaljsidan
export interface IncidentWithCI extends Incident {
    ci_name: string;
    ci_environment: string;
    ci_type: string;
    owner_name: string;
    owner_email: string;
}

export interface IncidentUpdate {
    id: number;
    incident_id: number;
    text: string;
    author_user_id: number | null;
    created_at: string;
}

export interface IncidentListFilter {
    status?: string;
    severity?: string;
    assignee_user_id?: number;
    unassigned_only?: boolean;
    ci_id?: number;
    sla_state?: string;
    search?: string;
    created_after?: string;
    created_before?: string;
    sort_by?: string;
    sort_dir?: string;
    page?: number;
    page_size?: number;
}

export interface IncidentListResult {
    incidents: Incident[];
    total_count: number;
    page: number;
    page_size: number;
}
