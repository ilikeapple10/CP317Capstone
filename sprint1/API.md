# Backend API for the Angular frontend

Base URL: `http://127.0.0.1:5050`

CORS is enabled for `http://localhost:4200` and `http://127.0.0.1:4200`.
Send cookies with every request (`withCredentials: true` in Angular `HttpClient`).

## Start the backend

```bash
cd sprint1
pip install -r requirements.txt
python3 app.py
```

## Endpoints

| Method | Path | Body / query | Returns |
|---|---|---|---|
| GET | `/api/health` | | `{ "ok": true }` |
| GET | `/api/products` | `?q=&category=` | products, categories, user |
| GET | `/api/cart` | | `{ items, total, count }` |
| POST | `/api/cart/add` | `{ "product_id": 1 }` | updated cart |
| POST | `/api/cart/update` | `{ "product_id": 1, "qty": 2 }` | updated cart (`qty` 0 removes) |
| POST | `/api/cart/remove` | `{ "product_id": 1 }` | updated cart |
| POST | `/api/account/consent` | `{ "consent": "accept" }` or `"decline"` | `{ accepted: true/false }` |
| POST | `/api/account` | name, email, password, role, preferred_category | new account (no password) |
| POST | `/api/login` | email, password | signed-in user |
| POST | `/api/logout` | | `{ ok: true }` |
| GET | `/api/me` | | current user and consent |
| GET | `/api/seller` | | seller user and `low_stock_alerts`, or 403 if not a seller |
| POST | `/api/seller/alerts` | `{ "enabled": true }` | saves the low-stock alert opt-in |
| GET | `/api/seller/listings` | | the seller's own listings |
| POST | `/api/seller/listings` | name, category, price, stock, description, image_url (optional, http/https) | new listing |
| DELETE | `/api/seller/listings/<id>` | | removes the seller's listing |
| POST | `/api/orders` | name, email, address, card_number (16 digits), expiry (`MM/YY`), cvv | order with `reference`; guests need consent first |
| GET | `/api/orders` | | signed-in user's orders, or 401 |
| POST | `/api/orders/lookup` | `{ "order_id": 1, "email": "..." }` | one order, so guests can find it later |
| GET | `/api/wishlist` | | signed-in user's saved products, or 401 |
| POST | `/api/wishlist` | `{ "product_id": 1 }` | saves a product |
| DELETE | `/api/wishlist/<id>` | | removes a saved product |

JSON and form bodies both work. Prefer JSON from Angular.

## Product shape

```json
{
  "id": 1,
  "name": "Wireless headphones",
  "category": "Electronics",
  "price": 39.0,
  "stock": 12,
  "label": "In stock",
  "description": null,
  "image_url": null
}
```

Payment is simulated. The card number is validated and never stored; the order keeps a
confirmation `reference` instead.

Starter products use a path to the frontend's own files for `image_url`, such as `assets/products/speaker.svg`.

## Angular example

```ts
this.http.get('http://127.0.0.1:5050/api/products', { withCredentials: true });
this.http.post(
  'http://127.0.0.1:5050/api/cart/add',
  { product_id: 1 },
  { withCredentials: true }
);
```

Account creation requires `POST /api/account/consent` with `"accept"` first.
Search and the cart work with no account.
