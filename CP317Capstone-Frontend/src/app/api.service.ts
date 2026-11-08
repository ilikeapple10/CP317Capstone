import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';

// Match the page hostname so session cookies work (localhost vs 127.0.0.1
// are different sites to the browser).
const BASE = `http://${typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1'}:5050`;
const opts = { withCredentials: true };

export interface Product {
  id: number;
  name: string;
  category: string;
  price: number;
  stock: number;
  label: string;
  description?: string | null;
  image_url?: string | null;
}

export interface CheckoutDetails {
  name: string;
  email: string;
  address: string;
  card_number: string;
  expiry: string;
  cvv: string;
}

export interface Cart {
  items: any[];
  total: number;
  count: number;
}

export interface ProductsResponse {
  products: Product[];
  categories: string[];
  user: any;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);

  getProducts(q = '', category = '') {
    // Always send q: without it the backend narrows the list to the shopper's preferred category.
    let params = new HttpParams().set('q', q);
    if (category) params = params.set('category', category);
    return this.http.get<ProductsResponse>(`${BASE}/api/products`, { ...opts, params });
  }

  getCart() {
    return this.http.get<Cart>(`${BASE}/api/cart`, opts);
  }
  addToCart(productId: number) {
    return this.http.post<Cart>(`${BASE}/api/cart/add`, { product_id: productId }, opts);
  }
  updateCart(productId: number, qty: number) {
    return this.http.post<Cart>(`${BASE}/api/cart/update`, { product_id: productId, qty }, opts);
  }
  removeFromCart(productId: number) {
    return this.http.post<Cart>(`${BASE}/api/cart/remove`, { product_id: productId }, opts);
  }

  consent(choice: 'accept' | 'decline') {
    return this.http.post<{ accepted: boolean }>(`${BASE}/api/account/consent`, { consent: choice }, opts);
  }
  createAccount(data: { name: string; email: string; password: string; role: string; preferred_category: string }) {
    return this.http.post(`${BASE}/api/account`, data, opts);
  }
  login(email: string, password: string) {
    return this.http.post<{ user: any }>(`${BASE}/api/login`, { email, password }, opts);
  }
  logout() {
    return this.http.post<{ ok: boolean }>(`${BASE}/api/logout`, {}, opts);
  }
  me() {
    return this.http.get<{ user: any; consent: string | null }>(`${BASE}/api/me`, opts);
  }
  placeOrder(details: CheckoutDetails) {
    return this.http.post<{ order_id: number; total: number; order: any }>(`${BASE}/api/orders`, details, opts);
  }
  lookupOrder(orderId: number, email: string) {
    return this.http.post<{ order: any }>(`${BASE}/api/orders/lookup`, { order_id: orderId, email }, opts);
  }
  getOrders() {
    return this.http.get<{ orders: any[] }>(`${BASE}/api/orders`, opts);
  }
  seller() {
    return this.http.get<{ user: any; low_stock_alerts: boolean }>(`${BASE}/api/seller`, opts);
  }
  setLowStockAlerts(enabled: boolean) {
    return this.http.post<{ low_stock_alerts: boolean }>(`${BASE}/api/seller/alerts`, { enabled }, opts);
  }
  getSellerListings() {
    return this.http.get<{ listings: any[] }>(`${BASE}/api/seller/listings`, opts);
  }
  addSellerListing(data: { name: string; category: string; price: number; stock: number; description: string; image_url: string }) {
    return this.http.post<{ listing: any }>(`${BASE}/api/seller/listings`, data, opts);
  }
  removeSellerListing(id: number) {
    return this.http.delete(`${BASE}/api/seller/listings/${id}`, opts);
  }

  getWishlist() {
    return this.http.get<{ items: Product[] }>(`${BASE}/api/wishlist`, opts);
  }
  addToWishlist(productId: number) {
    return this.http.post(`${BASE}/api/wishlist`, { product_id: productId }, opts);
  }
  removeFromWishlist(productId: number) {
    return this.http.delete(`${BASE}/api/wishlist/${productId}`, opts);
  }
}
