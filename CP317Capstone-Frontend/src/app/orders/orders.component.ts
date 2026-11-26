import { Component, inject, OnInit, signal } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../api.service';
import { switchMap } from 'rxjs';

@Component({
  selector: 'app-orders',
  standalone: true,
  imports: [CurrencyPipe, DatePipe, RouterLink],
  templateUrl: './orders.component.html',
  styleUrl: './orders.component.css',
})
export class OrdersComponent implements OnInit {
  private api = inject(ApiService);

  orders = signal<any[]>([]);
  error = signal('');
  // Guests (CHK-1) open an order with its number and checkout email instead of an account.
  guest = signal(false);
  loading = signal(true);

  isSeller = signal(false);
  updatingOrderId = signal<number | null>(null);



  ngOnInit() {
    this.api
      .currentRole()                               // Observable<'guest'|'shopper'|'seller'>
      .pipe(
        switchMap((role) => {
          this.isSeller.set(role === 'seller');
          if (role === 'seller') {
            return this.api.getSellerOrders();     // GET /api/seller/orders
          }
          if (role === 'shopper') {
            return this.api.getOrders();           // GET /api/orders
          }
          if (role === 'guest') {
            this.guest.set(true);
          }
          // Guest – return an empty observable (no auto‑load)

                    // or { orders: [] } for the guest case above.
          this.loading.set(false);
          return [] as any;
        })
      )
      .subscribe({
        next: (res: any) => {
          // `res` is { orders: [...] } (or empty array for guest)
          this.orders.set(res?.orders ?? []);
          this.loading.set(false);
        },
        error: (e: any) => {
          this.loading.set(false);
          if (e?.status === 401) {
            // 401 ⇒ not signed in → show the order‑lookup form
            this.guest.set(true);
          } else {
            this.error.set('Could not load orders.');
          }
        },
      });
  }

  lookup(event: Event, orderId: string, email: string) {
    event.preventDefault();
    this.api.lookupOrder(Number(orderId), email.trim()).subscribe({
      next: (res) => { this.error.set(''); this.orders.set([res.order]); },
      error: (e: any) => {
        this.orders.set([]);
        this.error.set(e?.error?.error ?? 'Could not look up that order.');
      },
    });
  }

changeStatus(orderId: number, newStatus: string): void {
    this.error.set('');
    this.updatingOrderId.set(orderId);
    this.api.updateSellerOrderStatus(orderId, newStatus).subscribe({
      next: () => {
        this.api.getSellerOrders().subscribe({
          next: (res) => {
            this.orders.set(res?.orders ?? []);
            this.updatingOrderId.set(null);
          },
          error: () => {
            this.updatingOrderId.set(null);
            this.error.set('Order updated, but could not refresh list.');
          },
        });
      },
      error: (e: any) => {
        this.updatingOrderId.set(null);
        this.error.set(e?.error?.error ?? 'Could not update order status.');
      },
    });
  }
}
