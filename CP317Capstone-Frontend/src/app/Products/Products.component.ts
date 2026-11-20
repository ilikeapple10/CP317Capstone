import { Component, inject, signal, OnInit } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { Router } from '@angular/router';
import { ApiService, Product } from '../api.service';
import { CartService } from '../cart.service';

@Component({
  selector: 'app-products',
  standalone: true,
  imports: [CurrencyPipe],
  templateUrl: './Products.component.html',
  styleUrl: './Products.component.css',
})
export class ProductsComponent implements OnInit {
  private api = inject(ApiService);
  private cart = inject(CartService);
  private router = inject(Router);

  products = signal<Product[]>([]);
  categories = signal<string[]>([]);
  error = signal('');
  loading = signal(true);
  missingImages = signal<Set<number>>(new Set());
  added = signal<number | null>(null);
  wished = signal<Set<number>>(new Set());

  ngOnInit() {
    this.load('', '');
  }

  apply(event: Event, query: string, category: string) {
    event.preventDefault();
    this.load(query.trim(), category);
  }

  add(p: Product) {
    this.cart.add(p.id).subscribe({
      next: () => {
        this.error.set('');
        this.added.set(p.id);
        setTimeout(() => this.added.set(null), 1200);
      },
      error: (e) => this.error.set(this.cart.errorMessage(e)),
    });
  }

  atLimit(p: Product) {
    return this.cart.qtyOf(p.id) >= p.stock;
  }

  canAdd(p: Product) {
    return p.stock > 0 && !this.atLimit(p);
  }

  labelFor(p: Product) {
    if (p.stock === 0) return 'Unavailable';
    if (this.atLimit(p)) return 'Max in cart';
    return this.added() === p.id ? 'Added' : 'Add to cart';
  }

  toggleWish(p: Product) {
    const on = this.wished().has(p.id);
    const request = on ? this.api.removeFromWishlist(p.id) : this.api.addToWishlist(p.id);
    request.subscribe({
      next: () =>
        this.wished.update((s) => {
          const next = new Set(s);
          on ? next.delete(p.id) : next.add(p.id);
          return next;
        }),
      error: (e: any) => {
        if (e?.status === 401) this.router.navigate(['/login']);
        else this.error.set('Could not update the wish list.');
      },
    });
  }

  imageFor(p: Product) {
    return p.image_url;
  }

  hasImage(p: Product) {
    return !!p.image_url && !this.missingImages().has(p.id);
  }

  onImageError(p: Product) {
    this.missingImages.update((s) => new Set(s).add(p.id));
  }

  private load(query: string, category: string) {
    this.api.getProducts(query, category).subscribe({
      next: (res) => {
        this.products.set(res.products);
        if (this.categories().length === 0) {
          this.categories.set(res.categories);
        }
        if (res.user && this.wished().size === 0) {
          this.api.getWishlist().subscribe({
            next: (w) => this.wished.set(new Set(w.items.map((i) => i.id))),
          });
        }
        this.error.set('');
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Could not reach the backend. Is it running on port 5050?');
        this.loading.set(false);
      },
    });
  }
}
