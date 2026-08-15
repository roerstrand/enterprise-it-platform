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
}

export interface IncidentUpdate {
    id: number;
    incident_id: number;
    text: string;
}