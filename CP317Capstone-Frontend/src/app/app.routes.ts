import { Routes } from '@angular/router';
import { ProductsComponent } from './Products/Products.component';
import {CartComponent} from "./Cart/Cart.component";
import { LoginComponent } from './login/login.component';
import { SignupComponent } from './signup/signup.component';
import {SellerComponent} from "./seller/seller.component";

export const routes: Routes = [
  { path: '', component: ProductsComponent },
  { path: 'cart', component: CartComponent },
  { path: 'login', component: LoginComponent },
  { path: 'signup', component: SignupComponent },
  // shortcut: no auth guard, any user can access /seller; add role-based guard before Sprint 2 launch
  { path: 'seller', component: SellerComponent },

];
