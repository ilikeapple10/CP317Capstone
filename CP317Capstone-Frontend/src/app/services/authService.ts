import { Injectable, computed, inject, signal } from '@angular/core';
import { catchError, finalize, of, switchMap, tap } from 'rxjs';
import { ApiService } from './apiService';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = inject(ApiService);

  private _user = signal<any | null>(null);
  user = this._user.asReadonly();
  isLoggedIn = computed(() => this._user() !== null);
  ready = signal(false); // true once we've asked the server who we are

  // Ask the server whether the session cookie is valid
  refresh() {
    return this.api.me().pipe(
      tap((res) => this._user.set(this.extractUser(res))),
      catchError(() => {
        this._user.set(null);
        return of(null);
      }),
      finalize(() => this.ready.set(true))
    );
  }

  ensureLoaded() {
    return this.ready() ? of(null) : this.refresh();
  }

  login(email: string, password: string) {
    return this.api.login(email, password).pipe(switchMap(() => this.refresh()));
  }

  logout() {
    return this.api.logout().pipe(finalize(() => this._user.set(null)));
  }

  private extractUser(res: any) {
    return res?.user ?? (res && Object.keys(res).length ? res : null);
  }
}
