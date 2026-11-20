import { Component, inject, OnInit, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { ApiService, Product } from '../api.service';
import { CartService } from '../cart.service';

@Component({
  selector: 'app-wishlist',
  standalone: true,
  imports: [CurrencyPipe, RouterLink],
  templateUrl: './wishlist.component.html',
  styleUrls: ['../seller/seller.component.css', './wishlist.component.css'],
})
export class WishlistComponent implements OnInit {
  private api = inject(ApiService);
  private router = inject(Router);
  private cart = inject(CartService);

  items = signal<Product[]>([]);
  error = signal('');
  loading = signal(true);

  ngOnInit() {
    this.api.getWishlist().subscribe({
      next: (res) => { this.items.set(res.items); this.loading.set(false); },
      error: (e: any) => {
        this.loading.set(false);
        if (e?.status === 401) this.router.navigate(['/login']);
        else this.error.set('Could not load your wish list.');
      },
    });
  }

  remove(p: Product) {
    this.api.removeFromWishlist(p.id).subscribe({
      next: () => this.items.update((list) => list.filter((i) => i.id !== p.id)),
      error: () => this.error.set('Could not remove that item.'),
    });
  }

  addToCart(p: Product) {
    this.cart.add(p.id).subscribe({
      next: () => this.error.set(''),
      error: (e) => this.error.set(this.cart.errorMessage(e)),
    });
  }
}
