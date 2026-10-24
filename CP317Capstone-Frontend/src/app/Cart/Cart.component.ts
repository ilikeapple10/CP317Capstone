import { Component, inject, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Observable } from 'rxjs';
import { CartService, CartLine } from '../cart.service';

@Component({
  selector: 'app-cart',
  standalone: true,
  imports: [CurrencyPipe, RouterLink],
  templateUrl: './Cart.component.html',
  styleUrl: './Cart.component.css',
})
export class CartComponent {
  cart = inject(CartService);
  error = signal('');

  atMax(line: CartLine) {
    return line.stock !== null && line.qty >= line.stock;
  }

  change(line: CartLine, delta: number) {
    const next = line.qty + delta;
    if (next < 1) return;
    if (line.stock !== null && next > line.stock) return;
    this.run(this.cart.setQty(line.productId, next));
  }

  remove(line: CartLine) {
    this.run(this.cart.remove(line.productId));
  }

  private run(request: Observable<unknown>) {
    request.subscribe({
      next: () => this.error.set(''),
      error: (e) => this.error.set(this.cart.errorMessage(e)),
    });
  }
}
