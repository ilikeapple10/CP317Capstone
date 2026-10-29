import { Component, inject, OnInit, signal } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
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
  private router = inject(Router);

  orders = signal<any[]>([]);
  error = signal('');

  ngOnInit() {
    this.api.getOrders().subscribe({
      next: (res) => this.orders.set(res.orders),
      error: (e: any) => {
        if (e?.status === 401) this.router.navigate(['/login']);
        else this.error.set('Could not load orders.');
      },
    });
  }
}
