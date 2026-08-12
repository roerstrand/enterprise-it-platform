import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CI } from './ci';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class CIService {
    private readonly baseUrl = `${environment.apiUrl}/demo/api/cis`;

    constructor(private http: HttpClient) {}

    list(): Observable<CI[]> {
        return this.http.get<CI[]>(this.baseUrl);
    }

    create(name: string, ciType: string, environment: string, ownerUserId: number | null): Observable<CI> {
        return this.http.post<CI>(this.baseUrl, {
            name,
            ci_type: ciType,
            environment,
            owner_user_id: ownerUserId
        });
    }

}