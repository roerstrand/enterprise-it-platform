import { Injectable, computed, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { CurrentUser, Role } from './current-user';

const TOKEN_KEY = 'auth_token';

interface JwtPayload {
    sub: string;
    email: string;
    role: Role;
    exp: number;
}

// Läser ut payload-delen av en JWT (mittendelen, base64url) utan att verifiera signaturen -
// verifiering sker redan server-side, klienten läser bara ut claims för UI-syften (visa roll, döljas etc).
function decodeJwt(token: string): JwtPayload | null {
    try {
        const payloadBase64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
        return JSON.parse(atob(payloadBase64));
    } catch {
        return null;
    }
}

function isExpired(payload: JwtPayload): boolean {
    return payload.exp * 1000 <= Date.now();
}

@Injectable({ providedIn: 'root' })
export class AuthService {
    private readonly baseUrl = `${environment.apiUrl}/demo/api`;

    // signal() istället för BehaviorSubject - Angulars egna reaktiva primitiv, funkar direkt i templates med t.ex. isAuthenticated()
    private readonly _currentUser = signal<CurrentUser | null>(this.readStoredUser());

    readonly currentUser = this._currentUser.asReadonly();
    readonly isAuthenticated = computed(() => this._currentUser() !== null);
    readonly isAdmin = computed(() => this._currentUser()?.role === 'admin');
    // Admin eller operator - de två roller som får mutera CI/incident/change
    readonly canManage = computed(() => {
        const role = this._currentUser()?.role;
        return role === 'admin' || role === 'operator';
    });

    constructor(private http: HttpClient) {}

    private readStoredUser(): CurrentUser | null {
        const token = localStorage.getItem(TOKEN_KEY);
        if (!token) return null;
        const payload = decodeJwt(token);
        if (!payload || isExpired(payload)) {
            localStorage.removeItem(TOKEN_KEY);
            return null;
        }
        return { id: Number(payload.sub), email: payload.email, role: payload.role };
    }

    getToken(): string | null {
        const token = localStorage.getItem(TOKEN_KEY);
        if (!token) return null;
        const payload = decodeJwt(token);
        if (!payload || isExpired(payload)) {
            return null;
        }
        return token;
    }

    login(email: string, password: string): Observable<{ access_token: string; token_type: string }> {
        return this.http.post<{ access_token: string; token_type: string }>(`${this.baseUrl}/login`, { email, password }).pipe(
            tap((response) => {
                const payload = decodeJwt(response.access_token);
                if (!payload) return;
                localStorage.setItem(TOKEN_KEY, response.access_token);
                this._currentUser.set({ id: Number(payload.sub), email: payload.email, role: payload.role });
            })
        );
    }

    logout(): void {
        localStorage.removeItem(TOKEN_KEY);
        this._currentUser.set(null);
    }
}
