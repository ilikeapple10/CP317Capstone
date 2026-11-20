import { Component, inject, OnInit, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../api.service';
import { CartService } from '../cart.service';

@Component({
  selector: 'app-checkout',
  standalone: true,
  imports: [CurrencyPipe, RouterLink],
  templateUrl: './checkout.component.html',
  styleUrls: ['../seller/seller.component.css', './checkout.component.css'],
})
export class CheckoutComponent implements OnInit {
  private api = inject(ApiService);
  cart = inject(CartService);

  user = signal<any>(null);
  // Guests see the data notice (USR-1) before entering personal details.
  needsConsent = signal(false);
  declined = signal(false);
  error = signal('');
  placed = signal<any>(null);
  ready = signal(false);
  placing = signal(false);

  ngOnInit() {
    this.cart.refresh();
    this.api.me().subscribe({
      next: (res) => {
        this.user.set(res.user);
        this.needsConsent.set(!res.user && res.consent !== 'accepted');
        this.ready.set(true);
      },
      error: () => {
        this.error.set('Could not reach the backend. Is it running on port 5050?');
        this.ready.set(true);
      },
    });
  }

  consent(choice: 'accept' | 'decline') {
    this.api.consent(choice).subscribe({
      next: (res) => {
        this.needsConsent.set(!res.accepted);
        this.declined.set(!res.accepted);
      },
      error: () => this.error.set('Could not save your choice.'),
    });
  }

  submit(event: Event, f: HTMLFormElement) {
    event.preventDefault();
    // A double click would otherwise send the same cart twice and place two orders.
    if (this.placing()) return;
    this.placing.set(true);
    const v = (name: string) => (f.elements.namedItem(name) as HTMLInputElement).value.trim();
    this.cart
      .checkout({
        name: v('name'),
        email: v('email'),
        address: v('address'),
        card_number: v('card_number'),
        expiry: v('expiry'),
        cvv: v('cvv'),
      })
      .subscribe({
        next: (res) => { this.error.set(''); this.placed.set(res.order); this.placing.set(false); },
        error: (e) => { this.error.set(this.cart.errorMessage(e)); this.placing.set(false); },
      });
  }
}
