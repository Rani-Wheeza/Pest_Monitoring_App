import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

/** App shell: top navigation for residents (Task 6.3) and the page outlet. */
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
      </nav>
    </header>
    <main>
      <router-outlet />
    </main>
  `,
})
export class App {}
