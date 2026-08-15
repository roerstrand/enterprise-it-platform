import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(),
    // Utan denna: inga ripple-effekter på knappar, inga mjuka övergångar i Material-komponenter -
    // allt känns "dött" trots att CSS-hover finns, eftersom Material internt kräver Angulars animationsmotor
    provideAnimationsAsync()
  ]
};
