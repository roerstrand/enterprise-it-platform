import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Incident } from './incident';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class IncidentService {
    private readonly baseUrl = `${environment.apiUrl}/demo/api/incidents`;

    constructor(private http: HttpClient) {}

    list(): Observable<Incident[]> {
        return this.http.get<Incident[]>(this.baseUrl);
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

    acceptSeverity(incidentId: number): Observable<Incident> {
        return this.http.post<Incident>(`${this.baseUrl}/${incidentId}/accept-severity`, {});
    }

    acceptStatus(incidentId: number): Observable<Incident> {
        return this.http.post<Incident>(`${this.baseUrl}/${incidentId}/accept-status`, {})
    }

}
