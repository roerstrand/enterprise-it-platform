import { CI } from './ci';
import { Incident } from '../incidents/incident';
import { Change } from '../changes/change';
import { AuditEvent } from '../audit/audit-event';

// GET /demo/api/cis/{id} - CI:t berikat med ägare, relationer och tvärgående drift-kontext
// (incidenter/changes/audit), aggregerat i gatewayen från CMDB+Incident+Change+Audit-tjänsterna.
export interface CIDetail extends CI {
    owner_name: string;
    owner_email: string;
    related_cis: CI[];
    incidents: Incident[];
    active_incidents: Incident[];
    changes: Change[];
    audit_events: AuditEvent[];
}
