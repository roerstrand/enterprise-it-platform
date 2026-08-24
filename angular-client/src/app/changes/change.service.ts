import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Change } from './change';
import { ChangeDetail } from './change-detail';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ChangeService {
    private readonly baseUrl = `${environment.apiUrl}/demo/api/changes`;

    constructor(private http: HttpClient) {}

    list(): Observable<Change[]> {
        return this.http.get<Change[]>(this.baseUrl);
    }

    getById(changeId: number): Observable<ChangeDetail> {
        return this.http.get<ChangeDetail>(`${this.baseUrl}/${changeId}`);
    }

    create(title: string, description: string, riskLevel: string, ciId: number): Observable<Change> {
        return this.http.post<Change>(this.baseUrl, {
            title,
            description,
            risk_level: riskLevel,
            ci_id: ciId,
        });
    }

    approve(changeId: number): Observable<Change> {
        return this.http.post<Change>(`${this.baseUrl}/${changeId}/approve`, {});
    }
}
