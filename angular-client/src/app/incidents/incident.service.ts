import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Incident, IncidentUpdate, IncidentWithCI } from './incident';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class IncidentService {
    private readonly baseUrl = `${environment.apiUrl}/demo/api/incidents`;

    constructor(private http: HttpClient) {}

    list(): Observable<Incident[]> {
        return this.http.get<Incident[]>(this.baseUrl);
    }

    getById(incidentId: number): Observable<IncidentWithCI> {
        return this.http.get<IncidentWithCI>(`${this.baseUrl}/${incidentId}`);
    }

    updateStatus(incidentId: number, status: string): Observable<Incident> {
        return this.http.put<Incident>(`${this.baseUrl}/${incidentId}/status`, { status });
    }

    updateSeverity(incidentId: number, severity: string): Observable<Incident> {
        return this.http.put<Incident>(`${this.baseUrl}/${incidentId}/severity`, { severity });
    }

    create(title: string, description: string, severity: string, ciId: number): Observable<Incident> {
        return this.http.post<Incident>(this.baseUrl, {
            title,
            description,
            severity,
            ci_id: ciId
        });
    }

    addUpdate(incidentId: number, text: string): Observable<Incident> {
        return this.http.post<Incident>(`${this.baseUrl}/${incidentId}/updates`, {
            text
        });
    }

    getUpdates(incidentId: number): Observable<IncidentUpdate[]> {
        return this.http.get<IncidentUpdate[]>(`${this.baseUrl}/${incidentId}/updates`);
    }

    acceptSeverity(incidentId: number): Observable<Incident> {
        return this.http.post<Incident>(`${this.baseUrl}/${incidentId}/accept-severity`, {});
    }

    acceptStatus(incidentId: number): Observable<Incident> {
        return this.http.post<Incident>(`${this.baseUrl}/${incidentId}/accept-status`, {})
    }

    update(incidentId: number, title: string, description: string, severity: string, ciId: number): Observable<Incident> {
        return this.http.put<Incident>(`${this.baseUrl}/${incidentId}`, {
            title,
            description,
            severity,
            ci_id: ciId
        });
    }

    delete(incidentId: number): Observable<unknown> {
        // ingen typad response behövs, backend returnerar bara { deleted: id } vi inte använder till något
        return this.http.delete(`${this.baseUrl}/${incidentId}`);
    }

}
