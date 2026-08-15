import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuditEvent } from './audit-event';
import { environment } from '../../environments/environment';

export interface AuditFilter {
    entityType?: string;
    entityId?: string;
    action?: string;
}

@Injectable({ providedIn: 'root' })
export class AuditService {
    private readonly baseUrl = `${environment.apiUrl}/demo/api/audit`;

    constructor(private http: HttpClient) {}

    list(filter: AuditFilter = {}): Observable<AuditEvent[]> {
        let params = new HttpParams();
        if (filter.entityType) params = params.set('entity_type', filter.entityType);
        if (filter.entityId) params = params.set('entity_id', filter.entityId);
        if (filter.action) params = params.set('action', filter.action);
        return this.http.get<AuditEvent[]>(this.baseUrl, { params });
    }
}
