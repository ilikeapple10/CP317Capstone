import { Component, inject, signal, OnInit } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
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

  products = signal<Product[]>([]);
  categories = signal<string[]>([]);
  error = signal('');
  missingImages = signal<Set<number>>(new Set());
  added = signal<number | null>(null);

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
    return this.added() === p.id ? 'Added ✓' : 'Add to cart';
  }

  imageFor(p: Product) {
    return `assets/products/${p.id}.jpg`;
  }

  hasImage(p: Product) {
    return !this.missingImages().has(p.id);
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
        this.error.set('');
      },
      error: () => this.error.set('Could not reach the backend. Is it running on port 5050?'),
    });
  }
}
