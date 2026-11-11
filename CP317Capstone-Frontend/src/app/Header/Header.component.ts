import { Component, inject, OnInit } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { CartService } from '../services/cartService';
import { AuthService } from '../services/authService';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './Header.component.html',
  styleUrl: './Header.component.css',
})
export class HeaderComponent implements OnInit {
  cart = inject(CartService);
  auth = inject(AuthService);
  private router = inject(Router);

  ngOnInit() {
    this.cart.refresh();
    this.auth.ensureLoaded().subscribe();
  }

  signOut() {
    this.auth.logout().subscribe({
      next: () => this.afterSignOut(),
      error: () => this.afterSignOut(), // still log out locally if the request fails
    });
  }

  private afterSignOut() {
    this.cart.refresh();          // the cart may be tied to the session
    this.router.navigate(['/']);
  }
}
