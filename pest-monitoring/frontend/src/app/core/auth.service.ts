import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { environment } from '../../environments/environment';

export interface CurrentUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
}

interface LoginResponse {
  token: string;
  user: CurrentUser;
}

const TOKEN_KEY = 'pestpatrol.token';
const USER_KEY = 'pestpatrol.user';

/** Username/password sign-in with a DRF API token (US-01, replaces the planned Entra ID sign-in). */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  // Restored from the browser on start-up, so refreshing the page keeps you signed in
  private readonly tokenValue = signal<string | null>(readStored(TOKEN_KEY));
  readonly user = signal<CurrentUser | null>(readStoredUser());
  readonly signedIn = computed(() => this.tokenValue() !== null);
  readonly isWorker = computed(() => ['Worker', 'Admin'].includes(this.user()?.role ?? ''));

  token(): string | null {
    return this.tokenValue();
  }

  login(username: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.base}/login/`, { username, password }).pipe(
      tap((response) => {
        this.tokenValue.set(response.token);
        this.user.set(response.user);
        writeStored(TOKEN_KEY, response.token);
        writeStored(USER_KEY, JSON.stringify(response.user));
      }),
    );
  }

  logout(): void {
    const token = this.tokenValue();
    if (token) {
      // Ask the server to delete the token (header set here because we forget it straight away);
      // signing out locally happens whatever the server answers
      const headers = new HttpHeaders({ Authorization: `Token ${token}` });
      this.http.post(`${this.base}/logout/`, {}, { headers }).subscribe({ error: () => undefined });
    }
    this.clear();
  }

  /** Forget the token and user without contacting the server (also used when the token is rejected). */
  clear(): void {
    this.tokenValue.set(null);
    this.user.set(null);
    writeStored(TOKEN_KEY, null);
    writeStored(USER_KEY, null);
  }
}

// localStorage can be blocked (private browsing, strict settings), so never let it break sign-in
function readStored(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function readStoredUser(): CurrentUser | null {
  try {
    const raw = readStored(USER_KEY);
    return raw ? (JSON.parse(raw) as CurrentUser) : null;
  } catch {
    return null;
  }
}

function writeStored(key: string, value: string | null): void {
  try {
    if (value === null) {
      localStorage.removeItem(key);
    } else {
      localStorage.setItem(key, value);
    }
  } catch {
    // Storage blocked: you stay signed in for this tab only
  }
}