import { Component, inject, OnInit, signal } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../api.service';

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

  ngOnInit() {
    this.api.getOrders().subscribe({
      next: (res) => { this.orders.set(res.orders); this.loading.set(false); },
      error: (e: any) => {
        this.loading.set(false);
        if (e?.status === 401) this.guest.set(true);
        else this.error.set('Could not load orders.');
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
}
