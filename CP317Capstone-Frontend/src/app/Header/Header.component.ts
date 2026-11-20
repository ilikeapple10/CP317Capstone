import { Component, inject, OnInit, signal } from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive } from '@angular/router';
import { ApiService } from '../api.service';
import { CartService } from '../cart.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './Header.component.html',
  styleUrl: './Header.component.css',
})
export class HeaderComponent implements OnInit {
  cart = inject(CartService);
  private api = inject(ApiService);
  private router = inject(Router);

  user = signal<any>(null);

  ngOnInit() {
    this.cart.refresh();
    this.loadUser();
    // Signing in happens on another page, so check again after each navigation.
    this.router.events.subscribe((e) => {
      if (e instanceof NavigationEnd) this.loadUser();
    });
  }

  signOut() {
    // A full reload clears everything loaded for the signed-in user, such as saved hearts.
    this.api.logout().subscribe({ next: () => window.location.assign('/') });
  }

  private loadUser() {
    this.api.me().subscribe({ next: (res) => this.user.set(res.user), error: () => {} });
  }
}
