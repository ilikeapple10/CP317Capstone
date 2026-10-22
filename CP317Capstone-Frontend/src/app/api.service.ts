import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';

const BASE = 'http://localhost:5050';
const opts = { withCredentials: true };

export interface Product {
  id: number;
  name: string;
  category: string;
  price: number;
  stock: number;
  label: string;
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
    let params = new HttpParams();
    if (q) params = params.set('q', q);
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
    return this.http.post(`${BASE}/api/login`, { email, password }, opts);
  }
  logout() {
    return this.http.post<{ ok: boolean }>(`${BASE}/api/logout`, {}, opts);
  }
  me() {
    return this.http.get(`${BASE}/api/me`, opts);
  }
  seller() {
    return this.http.get(`${BASE}/api/seller`, opts);
  }
}
