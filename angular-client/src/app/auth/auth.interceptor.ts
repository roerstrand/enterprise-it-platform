import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from './auth.service';

// Funktionell interceptor (Angular 21-stil) istället för en klass som implementerar HttpInterceptor -
// registreras med withInterceptors([authInterceptor]) i app.config.ts.
export const authInterceptor: HttpInterceptorFn = (req, next) => {
    const auth = inject(AuthService);
    const router = inject(Router);

    const token = auth.getToken();
    const authedReq = token
        ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
        : req;

    return next(authedReq).pipe(
        catchError((error) => {
            if (error.status === 401) {
                // Token saknas/har gått ut/är ogiltig - rensa lokalt state och skicka till login,
                // med returnUrl så guard:en kan skicka tillbaka hit efter lyckad inloggning.
                auth.logout();
                router.navigate(['/login'], { queryParams: { returnUrl: router.url } });
            }
            return throwError(() => error);
        })
    );
};
