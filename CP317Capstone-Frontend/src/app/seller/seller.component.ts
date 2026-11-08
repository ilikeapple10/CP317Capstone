import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { ApiService } from '../api.service';

interface Listing {
  id: number;
  name: string;
  category: string;
  price: number;
  stock: number;
  description?: string | null;
  pending?: boolean;
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
  loading = signal(true);
  saving = computed(() => this.listings().some((l) => l.pending));
  formError = signal('');
  alertDismissed = signal(false);
  // INV-1: the seller opts in to low-stock alerts; saved on their account.
  alertsOn = signal(false);

  lowStock = computed(() => this.listings().filter((l) => l.stock > 0 && l.stock < 5));
  outOfStock = computed(() => this.listings().filter((l) => l.stock === 0));
  totalUnits = computed(() => this.listings().reduce((n, l) => n + l.stock, 0));
  showAlert = computed(() => this.alertsOn() && !this.alertDismissed() && this.lowStock().length > 0);

  ngOnInit() {
    this.api.getSellerListings().subscribe({
      next: (res) => { this.listings.set(res.listings); this.loading.set(false); },
      error: () => { this.formError.set('Could not load listings.'); this.loading.set(false); },
    });
    this.api.seller().subscribe({ next: (res) => this.alertsOn.set(res.low_stock_alerts) });
  }

  setAlerts(enabled: boolean) {
    this.api.setLowStockAlerts(enabled).subscribe({
      next: (res) => { this.alertsOn.set(res.low_stock_alerts); this.alertDismissed.set(false); },
      error: () => this.formError.set('Could not save the alert setting.'),
    });
  }

  labelOf(l: Listing) {
    if (l.stock <= 0) return 'Out of stock';
    if (l.stock < 5) return 'Low stock';
    return 'In stock';
  }

  add(event: Event, form: HTMLFormElement, name: string, category: string, price: string, stock: string,
      description: string, imageUrl: string) {
    event.preventDefault();
    if (this.saving()) return;
    const p = Number(price);
    // Number('') is 0, which would list a blank stock field as out of stock.
    const s = stock.trim() === '' ? NaN : Number(stock);
    if (!name.trim() || !category || !Number.isFinite(p) || p <= 0 || !Number.isInteger(s) || s < 0) {
      this.formError.set('Enter a name, a category, a price above 0, and a whole-number stock.');
      return;
    }
    this.formError.set('');
    const data = { name: name.trim(), category, price: p, stock: s, description: description.trim(), image_url: imageUrl.trim() };
    // INV-2: show the item highlighted as pending until the backend validates and saves it.
    const tempId = -Date.now();
    this.listings.update((list) => [{ ...data, id: tempId, pending: true }, ...list]);
    this.api.addSellerListing(data).subscribe({
      next: (res) => {
        this.listings.update((list) => list.map((l) => (l.id === tempId ? res.listing : l)));
        form.reset();
      },
      error: (err: any) => {
        this.listings.update((list) => list.filter((l) => l.id !== tempId));
        this.formError.set(err.error?.error ?? 'Could not add listing.');
      },
    });
  }

  remove(id: number) {
    this.api.removeSellerListing(id).subscribe({
      next: () => this.listings.update((list) => list.filter((l) => l.id !== id)),
      error: () => this.formError.set('Could not remove listing.'),
    });
  }
}
