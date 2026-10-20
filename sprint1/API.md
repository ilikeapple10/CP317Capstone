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
| GET | `/api/seller` | | seller home, or 403 if not a seller |

JSON and form bodies both work. Prefer JSON from Angular.

## Product shape

```json
{
  "id": 1,
  "name": "Wireless headphones",
  "category": "Electronics",
  "price": 39.0,
  "stock": 12,
  "label": "In stock"
}
```

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
