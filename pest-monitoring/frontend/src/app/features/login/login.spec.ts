import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { Login } from './login';

describe('Login (US-01)', () => {
  let fixture: ComponentFixture<Login>;
  let http: HttpTestingController;
  let router: Router;

  beforeEach(() => {
    localStorage.removeItem('pestpatrol.token');
    localStorage.removeItem('pestpatrol.user');
    TestBed.configureTestingModule({
      imports: [Login],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([{ path: '**', children: [] }])],
    });
    http = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    fixture = TestBed.createComponent(Login);
    fixture.detectChanges();
  });

  afterEach(() => {
    http.verify();
    TestBed.inject(AuthService).clear();
  });

  function signInAs(username: string, password: string) {
    fixture.componentInstance.form.setValue({ username, password });
    fixture.componentInstance.submit();
  }

  it('asks for both fields before contacting the server', () => {
    fixture.componentInstance.submit();
    expect(fixture.componentInstance.error()).toBe('Enter your username and password.');
  });

  it('goes to My reports after signing in', () => {
    const navigate = spyOn(router, 'navigateByUrl').and.resolveTo(true);
    signInAs('aisha', 'pw');
    http.expectOne('/api/login/').flush({
      token: 'abc123',
      user: { id: 1, username: 'aisha', email: '', first_name: '', last_name: '', role: 'User' },
    });
    expect(navigate).toHaveBeenCalledWith('/my-reports');
  });

  it('shows a clear message for a wrong password', () => {
    signInAs('aisha', 'wrong');
    http.expectOne('/api/login/').flush({ non_field_errors: ['bad'] }, { status: 400, statusText: 'Bad Request' });
    expect(fixture.componentInstance.error()).toBe('Wrong username or password.');
    expect(fixture.componentInstance.busy()).toBeFalse();
  });

  it('says when the server cannot be reached', () => {
    signInAs('aisha', 'pw');
    http.expectOne('/api/login/').flush(null, { status: 0, statusText: 'Unknown Error' });
    expect(fixture.componentInstance.error()).toBe('Could not reach the server. Try again.');
  });
});