import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from './core/auth.service';

/** App shell: top navigation (Task 6.3), sign in / sign out, and the page outlet. */
@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="topbar">
      <a class="brand" routerLink="/">PestPatrol</a>
      <nav aria-label="Main">
        <a routerLink="/report" routerLinkActive="active">Report a sighting</a>
        <a routerLink="/map" routerLinkActive="active">Pest map</a>
        <a routerLink="/my-reports" routerLinkActive="active">My reports</a>
        @if (auth.signedIn()) {
          <span class="hint">Signed in as {{ auth.user()?.username }}</span>
          <button type="button" class="link" (click)="signOut()">Sign out</button>
        } @else {
          <a routerLink="/login" routerLinkActive="active">Sign in</a>
        }
      </nav>
    </header>
    <main>
      <router-outlet />
    </main>
  `,
})
export class App {
  readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  signOut(): void {
    this.auth.logout();
    this.router.navigate(['/report']);
  }
}