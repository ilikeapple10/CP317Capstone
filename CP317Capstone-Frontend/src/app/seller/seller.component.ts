import { Component, computed, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';

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
export class SellerComponent {
  categories = ['Electronics', 'Home', 'Apparel'];

  // TODO: replace with user's actual listings from backend. (Sprint 2)
  listings = signal<Listing[]>([
    { id: 1, name: 'Ceramic planter', category: 'Home', price: 18.0, stock: 24 },
    { id: 2, name: 'Bluetooth speaker', category: 'Electronics', price: 45.0, stock: 3 },
    { id: 3, name: 'Wool scarf', category: 'Apparel', price: 29.0, stock: 0 },
    { id: 4, name: 'Desk organizer', category: 'Home', price: 22.0, stock: 9 },
  ]);

  formError = signal('');
  alertDismissed = signal(false);
  private nextId = 100;

  lowStock = computed(() => this.listings().filter((l) => l.stock > 0 && l.stock < 5));
  outOfStock = computed(() => this.listings().filter((l) => l.stock === 0));
  totalUnits = computed(() => this.listings().reduce((n, l) => n + l.stock, 0));
  showAlert = computed(() => !this.alertDismissed() && this.lowStock().length > 0);

  labelOf(l: Listing) {
    if (l.stock <= 0) return 'Out of stock';
    if (l.stock < 5) return 'Low stock';
    return 'In stock';
  }

  // TODO: send to the backend instead of only updating page. (Sprint 2)
  add(event: Event, form: HTMLFormElement, name: string, category: string, price: string, stock: string) {
    event.preventDefault();
    const p = Number(price);
    const s = Number(stock);
    if (!name.trim() || !category || !Number.isFinite(p) || p <= 0 || !Number.isInteger(s) || s < 0) {
      this.formError.set('Enter a name, a category, a price above 0, and a whole-number stock.');
      return;
    }
    this.formError.set('');
    this.listings.update((list) => [
      { id: this.nextId++, name: name.trim(), category, price: p, stock: s },
      ...list,
    ]);
    form.reset();
  }

  // TODO: this is a placeholder function. need to integrate backend. (Sprint 2)
  remove(id: number) {
    this.listings.update((list) => list.filter((l) => l.id !== id));
  }
}
