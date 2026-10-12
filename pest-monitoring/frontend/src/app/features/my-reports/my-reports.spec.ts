import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { Sighting } from '../../core/models';
import { MyReports } from './my-reports';

const report = (id: number, resident_status: string) =>
  ({ id, reference: `PP-${id}`, species: 'Brown rat', resident_status, street_or_landmark: 'Lane',
     submitted_at: '2026-10-10T10:00:00Z' }) as Sighting;

describe('MyReports', () => {
  function create(api: Partial<ApiService>) {
    TestBed.configureTestingModule({
      imports: [MyReports],
      providers: [provideRouter([]), { provide: ApiService, useValue: api }],
    });
    const fixture = TestBed.createComponent(MyReports);
    fixture.detectChanges();
    return fixture;
  }

  it('counts reports by status', () => {
    const fixture = create({ mySightings: () => of({ count: 3, next: null, previous: null,
      results: [report(1, 'Awaiting review'), report(2, 'Resolved'), report(3, 'Awaiting review')] }) });
    const c = fixture.componentInstance;
    expect(c.reports().length).toBe(3);
    expect(c.countBy('Awaiting review')).toBe(2);
    expect(c.countBy('Resolved')).toBe(1);
    expect(fixture.nativeElement.textContent).toContain('PP-2');
  });

  it('asks the user to sign in when the API says 401', () => {
    const fixture = create({ mySightings: () => throwError(() => ({ status: 401 })) });
    expect(fixture.componentInstance.needsSignIn()).toBeTrue();
    expect(fixture.nativeElement.textContent).toContain('Sign in');
  });
});
