import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { Sighting } from '../../core/models';
import { badgeClass } from '../../core/report-rules';

/** "My pest reports" resident dashboard (Task 6, Figma frame 44-1826). */
@Component({
  selector: 'app-my-reports',
  imports: [DatePipe, RouterLink],
  template: `
    <section class="page">
      <div class="page-head">
        <div>
          <h1>My pest reports</h1>
          <p class="hint">Track updates from the response team.</p>
        </div>
        <a class="button primary" routerLink="/report">Submit another report</a>
      </div>

      @if (needsSignIn()) {
        <div class="card"><p>Sign in to see the reports you have submitted.</p></div>
      } @else {
        <div class="stats">
          <div class="stat"><strong>{{ reports().length }}</strong><span>Total reports</span></div>
          <div class="stat"><strong>{{ countBy('Awaiting review') }}</strong><span>Awaiting review</span></div>
          <div class="stat"><strong>{{ countBy('Response scheduled') }}</strong><span>Response scheduled</span></div>
          <div class="stat"><strong>{{ countBy('Resolved') }}</strong><span>Resolved</span></div>
        </div>

        <div class="card">
          <h2>Submitted reports</h2>
          @for (r of reports(); track r.id) {
            <article class="report-row">
              <div>
                <h3>{{ r.species }} sighting</h3>
                <p class="ref">#{{ r.reference }}</p>
                <p><strong>{{ r.street_or_landmark }}</strong></p>
                <p class="hint">Submitted {{ r.submitted_at | date: 'd MMM, h:mm a' }}</p>
              </div>
              <span [class]="badge(r.resident_status)">{{ r.resident_status }}</span>
            </article>
          } @empty {
            <p class="hint">No reports yet.</p>
          }
        </div>
      }
    </section>
  `,
})
export class MyReports implements OnInit {
  private readonly api = inject(ApiService);
  readonly reports = signal<Sighting[]>([]);
  readonly needsSignIn = signal(false);

  ngOnInit(): void {
    this.api.mySightings().subscribe({
      next: (page) => this.reports.set(page.results),
      error: (err: HttpErrorResponse) => this.needsSignIn.set(err.status === 401 || err.status === 403),
    });
  }

  countBy(status: string): number {
    return this.reports().filter((r) => r.resident_status === status).length;
  }

  badge(status: string): string {
    return badgeClass(status);
  }
}
