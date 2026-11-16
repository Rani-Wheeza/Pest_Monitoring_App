import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { App } from './app';

describe('App', () => {
  it('shows the navigation with a sign-in link when signed out', () => {
    localStorage.removeItem('pestpatrol.token');
    localStorage.removeItem('pestpatrol.user');
    TestBed.configureTestingModule({ imports: [App], providers: [provideRouter([]), provideHttpClient()] });
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('PestPatrol');
    expect(text).toContain('Report a sighting');
    expect(text).toContain('My reports');
    expect(text).toContain('Sign in');
  });
});