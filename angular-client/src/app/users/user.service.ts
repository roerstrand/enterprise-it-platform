import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { User } from './user';

@Injectable({ providedIn: 'root' })
export class UserService {
    private readonly baseUrl = '/demo/api/users';

    constructor(private http: HttpClient) {}

    list(): Observable<User[]> {
        return this.http.get<User[]>(this.baseUrl);
    }

    create(name: string, email: string, password: string): Observable<User> {
        return this.http.post<User>(this.baseUrl, { name, email, password });
    }
}