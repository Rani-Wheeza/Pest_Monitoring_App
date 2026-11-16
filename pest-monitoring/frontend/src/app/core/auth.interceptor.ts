import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { environment } from '../../environments/environment';
import { AuthService } from './auth.service';

/** Adds the sign-in token to every API call, and signs out if the server rejects the token. */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const token = auth.token();
  const isApiCall = req.url.startsWith(environment.apiUrl);

  // Only our own API gets the token, and never overwrite a header a caller set on purpose (logout)
  const outgoing =
    token && isApiCall && !req.headers.has('Authorization')
      ? req.clone({ setHeaders: { Authorization: `Token ${token}` } })
      : req;

  return next(outgoing).pipe(
    catchError((error: unknown) => {
      // 401 with a token means it was deleted or the account disabled: drop it and go to sign in
      if (error instanceof HttpErrorResponse && error.status === 401 && isApiCall && token) {
        auth.clear();
        router.navigate(['/login']);
      }
      return throwError(() => error);
    }),
  );
};