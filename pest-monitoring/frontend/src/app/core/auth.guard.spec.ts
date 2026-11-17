import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree, provideRouter } from '@angular/router';

import { authGuard } from './auth.guard';

describe('authGuard', () => {
  // Runs the guard the way the router would, for a visit to /my-reports
  function runGuard() {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideRouter([])] });
    return TestBed.runInInjectionContext(() =>
      authGuard({} as ActivatedRouteSnapshot, { url: '/my-reports' } as RouterStateSnapshot),
    );
  }

  afterEach(() => {
    localStorage.removeItem('pestpatrol.token');
  });

  it('sends signed-out users to sign in, remembering where they were going', () => {
    localStorage.removeItem('pestpatrol.token');
    const result = runGuard() as UrlTree;
    expect(result.root.children['primary'].segments[0].path).toBe('login');
    expect(result.queryParams['returnUrl']).toBe('/my-reports');
  });

  it('lets signed-in users through', () => {
    localStorage.setItem('pestpatrol.token', 'abc123');
    expect(runGuard()).toBeTrue();
  });
});