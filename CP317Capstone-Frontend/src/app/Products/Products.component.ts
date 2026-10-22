import { Component, inject, signal, OnInit } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { ApiService, Product } from '../api.service';

@Component({
  selector: 'app-products',
  standalone: true,
  imports: [CurrencyPipe],
  templateUrl: './Products.component.html',
  styleUrl: './Products.component.css',
})
export class ProductsComponent implements OnInit {
  private api = inject(ApiService);

  products = signal<Product[]>([]);
  categories = signal<string[]>([]);
  cartCount = signal(0);
  error = signal('');
  missingImages = signal<Set<number>>(new Set());

  ngOnInit() {
    this.load('', '');
    this.loadCart();
  }

  apply(event: Event, query: string, category: string) {
    event.preventDefault();
    this.load(query.trim(), category);
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

  private loadCart() {
    this.api.getCart().subscribe({
      next: (c) => {
        console.log('cart response', c);
        this.cartCount.set(this.countOf(c));
      },
      error: () => this.cartCount.set(0),
    });
  }

  // Tolerates a slightly different response shape, so the badge never shows blank.
  private countOf(c: any): number {
    if (typeof c?.count === 'number') return c.count;
    if (Array.isArray(c?.items)) {
      return c.items.reduce((n: number, i: any) => n + (i.qty ?? i.quantity ?? 1), 0);
    }
    return 0;
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
