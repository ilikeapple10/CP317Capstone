import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { ApiService } from '../api.service';

interface Listing {
  id: number;
  name: string;
  category: string;
  price: number;
  stock: number;
}

@Component({
  selector: 'app-seller',
  standalone: true,
  imports: [CurrencyPipe],
  templateUrl: './seller.component.html',
  styleUrl: './seller.component.css',
})
export class SellerComponent implements OnInit {
  private api = inject(ApiService);
  categories = ['Electronics', 'Home', 'Apparel'];

  listings = signal<Listing[]>([]);
  formError = signal('');
  alertDismissed = signal(false);

  lowStock = computed(() => this.listings().filter((l) => l.stock > 0 && l.stock < 5));
  outOfStock = computed(() => this.listings().filter((l) => l.stock === 0));
  totalUnits = computed(() => this.listings().reduce((n, l) => n + l.stock, 0));
  showAlert = computed(() => !this.alertDismissed() && this.lowStock().length > 0);

  ngOnInit() {
    this.api.getSellerListings().subscribe({
      next: (res) => this.listings.set(res.listings),
      error: () => this.formError.set('Could not load listings.'),
    });
  }

  labelOf(l: Listing) {
    if (l.stock <= 0) return 'Out of stock';
    if (l.stock < 5) return 'Low stock';
    return 'In stock';
  }

  add(event: Event, form: HTMLFormElement, name: string, category: string, price: string, stock: string) {
    event.preventDefault();
    const p = Number(price);
    const s = Number(stock);
    if (!name.trim() || !category || !Number.isFinite(p) || p <= 0 || !Number.isInteger(s) || s < 0) {
      this.formError.set('Enter a name, a category, a price above 0, and a whole-number stock.');
      return;
    }
    this.formError.set('');
    this.api.addSellerListing({ name: name.trim(), category, price: p, stock: s }).subscribe({
      next: (res) => {
        this.listings.update((list) => [res.listing, ...list]);
        form.reset();
      },
      error: (err: any) => this.formError.set(err.error?.error ?? 'Could not add listing.'),
    });
  }

  remove(id: number) {
    this.api.removeSellerListing(id).subscribe({
      next: () => this.listings.update((list) => list.filter((l) => l.id !== id)),
      error: () => this.formError.set('Could not remove listing.'),
    });
  }
}
