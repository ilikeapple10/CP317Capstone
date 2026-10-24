import { Component, inject, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CartService } from '../cart.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './Header.component.html',
  styleUrl: './Header.component.css',
})
export class HeaderComponent implements OnInit {
  cart = inject(CartService);

  ngOnInit() {
    this.cart.refresh();
  }
}
