export interface AuditEvent {
    id: number;
    timestamp: string;
    actor_user_id: number | null;
    actor_email: string | null;
    action: string;
    entity_type: string;
    entity_id: string;
    before: Record<string, unknown> | null;
    after: Record<string, unknown> | null;
}
