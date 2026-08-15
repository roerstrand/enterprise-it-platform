import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { User } from './user';
import { Role } from '../auth/current-user';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class UserService {
    private readonly baseUrl = `${environment.apiUrl}/demo/api/users`;

    constructor(private http: HttpClient) {}

    list(): Observable<User[]> {
        return this.http.get<User[]>(this.baseUrl);
    }

    create(name: string, email: string, password: string): Observable<User> {
        return this.http.post<User>(this.baseUrl, { name, email, password });
    }

    updateRole(userId: number, role: Role): Observable<User> {
        return this.http.put<User>(`${this.baseUrl}/${userId}/role`, { role });
    }
}