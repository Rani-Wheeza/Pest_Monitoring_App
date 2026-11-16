import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { authInterceptor } from './auth.interceptor';
import { AuthService, CurrentUser } from './auth.service';

const USER: CurrentUser = { id: 1, username: 'aisha', email: 'aisha@example.com', first_name: '', last_name: '', role: 'User' };

describe('AuthService and authInterceptor (US-01)', () => {
  let auth: AuthService;
  let http: HttpTestingController;
  let client: HttpClient;

  beforeEach(() => {
    localStorage.removeItem('pestpatrol.token');
    localStorage.removeItem('pestpatrol.user');
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        provideRouter([{ path: '**', children: [] }]),
      ],
    });
    auth = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
    client = TestBed.inject(HttpClient);
  });

  afterEach(() => {
    http.verify();
    auth.clear();
  });

  function signIn() {
    auth.login('aisha', 'pw').subscribe();
    http.expectOne('/api/login/').flush({ token: 'abc123', user: USER });
  }

  it('stores the token and user after signing in', () => {
    auth.login('aisha', 'pw').subscribe();
    const req = http.expectOne('/api/login/');
    expect(req.request.body).toEqual({ username: 'aisha', password: 'pw' });
    req.flush({ token: 'abc123', user: USER });
    expect(auth.signedIn()).toBeTrue();
    expect(auth.user()?.username).toBe('aisha');
    expect(localStorage.getItem('pestpatrol.token')).toBe('abc123');
  });

  it('adds the token to API calls', () => {
    signIn();
    client.get('/api/me/').subscribe();
    expect(http.expectOne('/api/me/').request.headers.get('Authorization')).toBe('Token abc123');
  });

  it('does not add a token when signed out', () => {
    client.get('/api/species/').subscribe();
    expect(http.expectOne('/api/species/').request.headers.has('Authorization')).toBeFalse();
  });

  it('signs out when the server rejects the token', () => {
    signIn();
    client.get('/api/me/').subscribe({ error: () => undefined });
    http.expectOne('/api/me/').flush({}, { status: 401, statusText: 'Unauthorized' });
    expect(auth.signedIn()).toBeFalse();
  });

  it('tells the server and forgets the token on sign out', () => {
    signIn();
    auth.logout();
    const req = http.expectOne('/api/logout/');
    expect(req.request.headers.get('Authorization')).toBe('Token abc123');
    req.flush(null, { status: 204, statusText: 'No Content' });
    expect(auth.signedIn()).toBeFalse();
    expect(localStorage.getItem('pestpatrol.token')).toBeNull();
  });
});