import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { App } from './app';

describe('App', () => {
  it('shows the navigation', () => {
    TestBed.configureTestingModule({ imports: [App], providers: [provideRouter([])] });
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('PestPatrol');
    expect(text).toContain('Report a sighting');
    expect(text).toContain('My reports');
  });
});
