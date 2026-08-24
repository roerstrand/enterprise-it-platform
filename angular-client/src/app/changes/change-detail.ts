import { Change } from './change';
import { Incident } from '../incidents/incident';

// GET /demo/api/changes/{id} - Changen berikad med incidenter länkade till den (löst upp via
// Incident Service, ingen incident-data dupplicerad i ChangeService)
export interface ChangeDetail extends Change {
    related_incidents: Incident[];
}
