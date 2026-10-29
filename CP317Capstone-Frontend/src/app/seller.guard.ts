import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';
import { ApiService } from './api.service';

export const sellerGuard = () => {
  const api = inject(ApiService);
  const router = inject(Router);
  return api.seller().pipe(
    map(() => true),
    catchError(() => of(router.createUrlTree(['/login']))),
  );
};
