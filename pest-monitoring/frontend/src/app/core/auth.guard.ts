import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

/** Pages that need an account send signed-out users to sign in, then back to where they were going. */
export const authGuard: CanActivateFn = (_route, state) => {
  if (inject(AuthService).signedIn()) {
    return true;
  }
  return inject(Router).createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
};