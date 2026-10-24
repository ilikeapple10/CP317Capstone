import { Injectable, inject, signal, computed } from '@angular/core';
import { tap } from 'rxjs';
import { ApiService } from './api.service';

export interface CartLine {
  productId: number;
  name: string;
  price: number;
  qty: number;
  stock: number | null;
}

@Injectable({ providedIn: 'root' })
export class CartService {
  private api = inject(ApiService);

  lines = signal<CartLine[]>([]);

  count = computed(() => this.lines().reduce((n, l) => n + l.qty, 0));

  subtotal = computed(
    () => Math.round(this.lines().reduce((s, l) => s + l.price * l.qty, 0) * 100) / 100
  );

  refresh() {
    this.api.getCart().subscribe({ next: (res) => this.apply(res), error: () => {} });
  }

  add(productId: number) {
    return this.api.addToCart(productId).pipe(tap((res) => this.apply(res)));
  }

  setQty(productId: number, qty: number) {
    return this.api.updateCart(productId, qty).pipe(tap((res) => this.apply(res)));
  }

  remove(productId: number) {
    return this.api.removeFromCart(productId).pipe(tap((res) => this.apply(res)));
  }

  qtyOf(productId: number): number {
    return this.lines().find((l) => l.productId === productId)?.qty ?? 0;
  }

  errorMessage(e: any): string {
    const m = e?.error?.error;
    if (typeof m === 'string' && m) return m;
    if (e?.status === 0) return 'Could not reach the backend. Is it running on port 5050?';
    return `Cart update failed (status ${e?.status}).`;
  }

  // GET /api/Cart returns the Cart directly; add/update/remove return { message, Cart }.
  private apply(res: any) {
    const cart = res?.cart ?? res;
    const items: any[] = Array.isArray(cart?.items) ? cart.items : [];
    this.lines.set(
      items.map((i) => ({
        productId: Number(i.id),
        name: String(i.name),
        price: Number(i.price),
        qty: Number(i.qty),
        stock: Number(i.stock),
      }))
    );
  }
}
