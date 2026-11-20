import { Routes } from '@angular/router';
import { ProductsComponent } from './Products/Products.component';
import {CartComponent} from "./Cart/Cart.component";
import { LoginComponent } from './login/login.component';
import { SignupComponent } from './signup/signup.component';
import {SellerComponent} from "./seller/seller.component";
import { sellerGuard } from './seller.guard';
import { OrdersComponent } from './orders/orders.component';
import { CheckoutComponent } from './checkout/checkout.component';
import { WishlistComponent } from './wishlist/wishlist.component';

export const routes: Routes = [
  { path: '', component: ProductsComponent },
  { path: 'cart', component: CartComponent },
  { path: 'login', component: LoginComponent },
  { path: 'signup', component: SignupComponent },
  { path: 'checkout', component: CheckoutComponent },
  { path: 'orders', component: OrdersComponent },
  { path: 'wishlist', component: WishlistComponent },
  { path: 'seller', component: SellerComponent, canActivate: [sellerGuard] },

];
