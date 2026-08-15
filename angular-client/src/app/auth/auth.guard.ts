import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

// Funktionell guard - Angular 21 föredrar detta över den äldre class-baserade CanActivate.
export const authGuard: CanActivateFn = (_route, state) => {
    const auth = inject(AuthService);
    const router = inject(Router);

    if (auth.isAuthenticated()) {
        return true;
    }
    // returnUrl = sidan användaren faktiskt försökte nå - login.ts läser denna efter lyckad inloggning
    return router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
};

// Extra spärr utöver authGuard, för rutter som bara Admin får se (t.ex. /audit).
export const adminGuard: CanActivateFn = (_route, state) => {
    const auth = inject(AuthService);
    const router = inject(Router);

    if (auth.isAdmin()) {
        return true;
    }
    if (!auth.isAuthenticated()) {
        return router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
    }
    return router.createUrlTree(['/']);
};
