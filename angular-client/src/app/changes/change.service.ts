import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Change } from './change';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ChangeService {
    private readonly baseUrl = `${environment.apiUrl}/demo/api/changes`;

    constructor(private http: HttpClient) {}

    list(): Observable<Change[]> {
        return this.http.get<Change[]>(this.baseUrl);
    }
}
