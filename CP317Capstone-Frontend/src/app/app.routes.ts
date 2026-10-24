import { Routes } from '@angular/router';
import { ProductsComponent } from './Products/Products.component';
import {CartComponent} from "./Cart/Cart.component";

export const routes: Routes = [
  { path: '', component: ProductsComponent },
  { path: 'cart', component: CartComponent },

];
