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
