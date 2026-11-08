# Wilfrid Laurier University
## CP317A Group Project – E-Commerce Application
### Sprint 01: Implementation and Initial Prototype

**Course code:** CP317A
**Project title:** E-Commerce Application
**Group ID:** Group G49
**Due date:** October 30, 2026

| Name | Role |
|---|---|
| Tai, Ethan | Scrum Master |
| **Tai, Austin** | **Product Owner** |
| Coufie, Stephen | Developer |

---

## 1. Sprint Goal

**Sprint objective:** Deliver a working first prototype of the G49 marketplace where a shopper can search the catalogue, manage a cart and check out, create an account (with data-collection consent) and log in, and a seller can manage their product listings, all connected to a shared database through a Flask REST API and an Angular frontend.

**Why these items were prioritized:**
- **Search and cart are the core buyer path.** Every later feature (product pages, wishlist, order tracking, reviews) depends on products being listed, found, and added to a cart.
- **Accounts and login unlock everything role-specific.** Sellers, order history, and wishlists all need a signed-in user, so authentication had to come first.
- **Consent was flagged as high priority in Milestone 02.** Our ethical considerations required the consent notice to exist before any real user data is collected, so it was built together with account creation.
- **Seller listings supply the catalogue.** Without a way for sellers to add products, the marketplace has nothing to sell.
- Three of the stories (UI-1, UI-3, INV-2) are rated **High** priority in our backlog. USR-2 is Medium, but sellers need an account before they can list products, so it had to come in Sprint 1 with INV-2.
- These stories also let us set up the full stack (database → Flask API → Angular UI) in one sprint, which later sprints build on.

---

## 2. Sprint Backlog

Sprint 1 stories come from the Milestone 02 Product Backlog. Four were planned for Sprint 1. **USR-1 (Data Collection Opt-In)** was moved up from Sprint 3, because account creation (USR-2) collects personal data and our ethical considerations require consent before that happens. The Excel Product Backlog has been updated so all five stories show **Sprint = "Sprint 1"**, and the Sprint 1 sheet lists their tasks.

| Story ID & Title | Points | Priority | Assigned | Tasks | Status |
|---|---|---|---|---|---|
| **UI-1** – Product Search | 3 | High | Ethan Tai, Stephen Coufie | • UI-1.1 Create `products` table and seed data • UI-1.2 `GET /api/products?q=&category=` endpoint • UI-1.3 Angular Products page with search bar and category dropdown • UI-1.4 Show name, price and availability for each product | Done |
| **UI-3** – Shopping Cart | 3 | High | Ethan Tai, Stephen Coufie | • UI-3.1 Session cart with add / update / remove endpoints • UI-3.2 Cap quantity at stock and calculate subtotal • UI-3.3 Angular Cart component • UI-3.4 Shared Header with cart count | Done |
| **USR-2** – Account Creation | 3 | Medium | Austin Tai, Stephen Coufie | • USR-2.1 `accounts` table with role (shopper / seller) • USR-2.2 Salted PBKDF2 password hashing • USR-2.3 Sign-up, login, logout, current-user endpoints • USR-2.4 Angular Login and Signup pages (show-password, confirm password, continue as guest) | Done |
| **INV-2** – Product Listing | 8 | High | Ethan Tai, Stephen Coufie | • INV-2.1 Seller-only listing endpoints (403 for non-sellers) • INV-2.2 Angular Seller dashboard: load, add, remove listings • INV-2.3 Route guard on `/seller` • INV-2.4 Image and description fields • INV-2.5 "Pending validation" highlight on new listings | In Progress |
| **USR-1** – Data Collection Opt-In *(moved up from Sprint 3)* | 1 | High | Stephen Coufie | • USR-1.1 Consent notice naming the data and its purpose • USR-1.2 Accept / decline endpoint • USR-1.3 Block account creation until accepted; search and cart still work on decline • USR-1.4 Show the notice at checkout (with CHK-2) | In Progress |

**Sprint 1 total:** 18 story points: 9 Done (UI-1, UI-3, USR-2) and 9 In Progress (INV-2, USR-1) carried into Sprint 2.

---

## 3. Implementation Progress

### What was built

**Backend (Flask + SQLite, `sprint1/app.py`)**
- SQLite database with `products`, `accounts`, and order tables, created and seeded on startup.
- A JSON REST API (documented in `sprint1/API.md`) with CORS enabled for the Angular dev server, using session cookies for cart and login state.
- Keyword + category product search, session cart with stock limits, consent flow, account creation with hashed passwords, login/logout, seller-only listing management, and order placement.

**Frontend (Angular, `CP317Capstone-Frontend/`)**
- Products page (search bar + category dropdown) connected to the backend.
- Cart page and a shared Header component showing the cart count.
- Login and Signup pages with show-password toggle, confirm-password check, and "continue as guest".
- Seller dashboard (load, add, remove listings) protected by a route guard.
- Orders page showing order history after checkout.
- A shared colour palette guide for consistent styling across components.

### Code snippets

**Database connection (one connection per request):**
```python
def connect():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    if "db" not in g:
        g.db = connect()
    return g.db
```

**Keyword and category search (parameterized SQL, safe from injection):**
```python
sql = "SELECT * FROM products WHERE 1 = 1"
params = []
if keyword:
    sql += " AND name LIKE ?"
    params.append(f"%{keyword}%")
if category:
    sql += " AND category = ?"
    params.append(category)
```

**Password hashing (salted PBKDF2, never stored in plain text):**
```python
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${digest}"
```

**Cart quantity capped at available stock:**
```python
elif qty > product["stock"]:
    cart[product_id] = product["stock"]
    message = f"Only {product['stock']} in stock. The quantity was kept at that number."
```

**Angular route guard for the seller dashboard:**
```ts
export const sellerGuard = () => {
  const api = inject(ApiService);
  const router = inject(Router);
  return api.seller().pipe(
    map(() => true),
    catchError(() => of(router.createUrlTree(['/login']))),
  );
};
```

*[Insert screenshots here: Products search page, Cart page, Signup/Login page, Seller dashboard, Orders page]*

### Technical issues and how they were resolved

| Issue | Resolution |
|---|---|
| The Angular app (port 4200) and Flask API (port 5050) run on different origins, so browser requests were blocked and session cookies were not sent. | Enabled CORS for `localhost:4200` with credentials in Flask, and sent every request with `withCredentials: true` in Angular `HttpClient`. |
| After signing up, the user was not kept logged in and the signup form failed in the local Angular + Flask setup. | Fixed session handling so the session is set on account creation and cookies persist across requests. |
| Role naming was inconsistent between the frontend and backend ("customer" vs "shopper"). | Standardized on `shopper` and `seller` across the database, API and UI. |
| "Continue as guest" and the confirm-password check on signup did not work correctly. | Fixed in the Signup component; guests can now search and use the cart without an account. |
| The `/seller` page could be opened by anyone, even though the API rejected non-sellers. | Added an Angular route guard that calls `/api/seller` and redirects non-sellers to the login page. |
| Team members working on separate features at the same time. | Used one Git branch per story (e.g. `UI-1`, `UI-3`, `USR-2`, `INV-2`) and merged through pull requests on GitHub. |

### Started early
- Part of **CHK-2 (Checkout, Sprint 2)**: a signed-in shopper can place an order from the cart (stock is checked and reduced), and the `/orders` page shows order history. Shipping and simulated payment fields are not built yet.

### Deferred to future sprints
- **INV-2** remainder: image and description on listings, and the "pending validation" highlight (Sprint 2).
- **USR-1** remainder: show the consent notice at checkout, together with CHK-2 (Sprint 2).
- Product detail page with full image, description, and verified-buyer reviews.
- Wishlist saved across sessions.
- Live order tracking with seller-updated delivery statuses.
- Seller sales-frequency summary and low-stock notifications.
- Login security hardening (account lock-out, optional 2FA, CAPTCHA on suspicious activity).
- Real payment processing (checkout currently validates fields only).
- Product images on listings and catalogue thumbnails.

---

## 4. Testing and Review

### How functionality was verified
- **Automated unit tests** (`sprint1/test_app.py`, Python `unittest`): 6 tests run against a fresh temporary database. All 6 pass (`python3 -m unittest test_app`).
  - Keyword search and category filter return only matching products.
  - Cart quantity is capped at stock and the subtotal is correct.
  - Declining consent creates no account and search stays available.
  - Shopper preferred category is applied and non-sellers are blocked from seller pages.
  - The products JSON API returns the expected product shape.
  - The cart and consent flow works through the JSON API.
- **Manual testing** of each Angular page against the running backend (search, add to cart, change quantity, remove, sign up, log in, log out, seller add/remove, checkout, view orders).
- **User simulation**: the Product Owner walked through the app as a guest shopper, a registered shopper, and a seller to confirm each story's acceptance criteria.

### Results per story

| Story | Acceptance criteria checked | Result | PO acceptance |
|---|---|---|---|
| UI-1 Product Search | Shopper can type a keyword and select a category filter to view a list of matching products | Pass | Done |
| UI-3 Shopping Cart | Shopper can add products, change quantities (up to stock), see an accurate subtotal, and proceed to checkout | Pass | Done |
| USR-2 Account Creation | User can create an account with name, email and password; password stored as a salted hash; guest use still works; login and logout work | Pass | Done |
| INV-2 Product Listing | Seller can list an item and it appears and is searchable on the marketplace; non-sellers are blocked | Pass (name, category, price, stock) / Fail (image, description, pending highlight not built) | Pending |
| USR-1 Data Collection Opt-In | Notice names the data and purpose; account cannot be created without consent; declining does not block search or the cart | Pass (account creation) / Not yet tested at checkout | Pending |

### How acceptance criteria were checked
Each story's acceptance criteria from the Milestone 02 backlog were turned into a checklist. Criteria that can be automated (search results, stock cap, consent gate, role checks) are covered by the unit tests above. The rest (page layout, navigation, form feedback) were checked manually by the developers and then demonstrated to the Product Owner, who marked each story Done or Pending in the backlog.
