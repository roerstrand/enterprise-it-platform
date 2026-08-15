import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { MAT_FORM_FIELD_DEFAULT_OPTIONS } from '@angular/material/form-field';

import { routes } from './app.routes';
import { authInterceptor } from './auth/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    // authInterceptor lägger på Authorization-header på alla anrop och loggar ut vid 401
    provideHttpClient(withInterceptors([authInterceptor])),
    // Utan denna: inga ripple-effekter på knappar, inga mjuka övergångar i Material-komponenter -
    // allt känns "dött" trots att CSS-hover finns, eftersom Material internt kräver Angulars animationsmotor
    provideAnimationsAsync(),
    // floatLabel: 'always' - labeln ligger alltid som en liten rubrik ovanför fältet,
    // istället för Materials default där en tom/ofokuserad ruta visar labeln stor och
    // centrerad (som ser ut som placeholder-text). Satt en gång globalt här istället
    // för som attribut på varje enskilt <mat-form-field> i varje formulär.
    { provide: MAT_FORM_FIELD_DEFAULT_OPTIONS, useValue: { floatLabel: 'always' } }
  ]
};
