import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, input, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../core/auth.service';

/** Sign-in page (US-01). Reporting a sighting never needs an account; My reports and worker pages do. */
@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule],
  template: `
    <section class="page">
      <div class="card">
        <h1>Sign in</h1>
        <form [formGroup]="form" (ngSubmit)="submit()" novalidate>
          <div class="field">
            <label for="username">Username</label>
            <input id="username" formControlName="username" autocomplete="username" />
          </div>
          <div class="field">
            <label for="password">Password</label>
            <input id="password" type="password" formControlName="password" autocomplete="current-password" />
          </div>
          @if (error()) {
            <p class="error" role="alert">{{ error() }}</p>
          }
          <button type="submit" class="primary" [disabled]="busy()">{{ busy() ? 'Signing in…' : 'Sign in' }}</button>
        </form>
        <p class="hint">You don't need an account to report a sighting.</p>
      </div>
    </section>
  `,
})
export class Login {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  // Filled from ?returnUrl=… by withComponentInputBinding(), so you land back where you started
  readonly returnUrl = input<string>();
  readonly error = signal('');
  readonly busy = signal(false);
  readonly form = inject(FormBuilder).nonNullable.group({
    username: ['', Validators.required],
    password: ['', Validators.required],
  });

  submit(): void {
    if (this.form.invalid) {
      this.error.set('Enter your username and password.');
      return;
    }
    this.busy.set(true);
    this.error.set('');
    const { username, password } = this.form.getRawValue();
    this.auth.login(username, password).subscribe({
      next: () => this.router.navigateByUrl(this.returnUrl() || '/my-reports'),
      error: (err: HttpErrorResponse) => {
        this.busy.set(false);
        // DRF answers 400 for a wrong password or a disabled account
        this.error.set(err.status === 400 ? 'Wrong username or password.' : 'Could not reach the server. Try again.');
      },
    });
  }
}