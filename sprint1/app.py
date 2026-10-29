"""Sprint 1 store: HTML pages plus JSON /api routes for the Angular frontend."""

import hashlib
import os
import secrets
import sqlite3
from pathlib import Path

from flask import Flask, flash, g, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS

BASE = Path(__file__).resolve().parent

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "g49-sprint1-dev")
app.config["DATABASE"] = os.environ.get("DATABASE", str(BASE / "store.db"))

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:4200",
                "http://127.0.0.1:4200",
                "http://localhost:4201",
                "http://127.0.0.1:4201",
                "http://localhost:4202",
                "http://127.0.0.1:4202",
            ]
        }
    },
    supports_credentials=True,
)

SEED = [
    ("Wireless headphones", "Electronics", 39.00, 12),
    ("Speaker", "Electronics", 59.00, 20),
    ("Running shoes", "Apparel", 64.00, 4),
    ("Desk lamp", "Home", 25.00, 15),
    ("Coffee mug", "Home", 12.00, 30),
    ("Winter jacket", "Apparel", 89.00, 0),
]


def connect():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    if "db" not in g:
        g.db = connect()
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = connect()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            preferred_category TEXT
        );
        """
    )
    try:
        db.execute("ALTER TABLE products ADD COLUMN seller_id INTEGER")
        db.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        db.executemany(
            "INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)",
            SEED,
        )
    db.commit()
    db.close()


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${digest}"


def check_password(password, stored):
    salt, digest = stored.split("$", 1)
    test = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return secrets.compare_digest(test, digest)


def stock_label(stock):
    if stock <= 0:
        return "Out of stock"
    if stock < 5:
        return "Low stock"
    return "In stock"


def product_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "price": row["price"],
        "stock": row["stock"],
        "label": stock_label(row["stock"]),
    }


def user_dict(user):
    if not user:
        return None
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "preferred_category": user.get("preferred_category"),
    }


def cart_payload():
    items, total = cart_lines()
    return {
        "items": items,
        "total": total,
        "count": sum(item["qty"] for item in items),
    }


def cart_lines():
    cart = session.get("cart", {})
    db = get_db()
    items = []
    for product_id, qty in cart.items():
        product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if product is None:
            continue
        qty = int(qty)
        items.append(
            {
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "stock": product["stock"],
                "qty": qty,
                "line": round(product["price"] * qty, 2),
                "label": stock_label(product["stock"]),
            }
        )
    total = round(sum(item["line"] for item in items), 2)
    return items, total


def categories():
    rows = get_db().execute("SELECT DISTINCT category FROM products ORDER BY category")
    return [row[0] for row in rows]


def request_data():
    """Read JSON body fields, or fall back to form fields."""
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict()


def query_products(keyword="", category="", use_preference=False):
    user = session.get("user") or {}
    if use_preference and not keyword and not category:
        category = user.get("preferred_category") or ""
    sql = "SELECT * FROM products WHERE 1 = 1"
    params = []
    if keyword:
        sql += " AND name LIKE ?"
        params.append(f"%{keyword}%")
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY name"
    return get_db().execute(sql, params).fetchall(), keyword, category


@app.context_processor
def inject_nav():
    cart = session.get("cart", {})
    count = sum(int(qty) for qty in cart.values())
    return {"cart_count": count, "current_user": session.get("user")}


# ----- HTML pages (unchanged for Sprint 1 demos) -----

@app.get("/")
def search():
    keyword = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    use_pref = request.args.get("q") is None and request.args.get("category") is None
    products, keyword, category = query_products(keyword, category, use_preference=use_pref)
    return render_template(
        "search.html",
        products=products,
        categories=categories(),
        keyword=keyword,
        category=category,
        stock_label=stock_label,
    )


@app.post("/cart/add")
def add_to_cart():
    product_id = request.form.get("product_id", "")
    product = get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None or product["stock"] <= 0:
        flash("That product is not available.")
        return redirect(url_for("search"))
    cart = session.setdefault("cart", {})
    current = int(cart.get(product_id, 0))
    if current + 1 > product["stock"]:
        flash(f"Only {product['stock']} in stock.")
    else:
        cart[product_id] = current + 1
        session["cart"] = cart
        flash(f"Added {product['name']} to the cart.")
    return redirect(request.referrer or url_for("search"))


@app.get("/cart")
def view_cart():
    items, total = cart_lines()
    return render_template("cart.html", items=items, total=total)


@app.post("/cart/update")
def update_cart():
    product_id = request.form.get("product_id", "")
    qty = request.form.get("qty", type=int)
    product = get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    cart = session.get("cart", {})
    if product is None or qty is None or qty <= 0:
        cart.pop(product_id, None)
    elif qty > product["stock"]:
        cart[product_id] = product["stock"]
        flash(f"Only {product['stock']} in stock. The quantity was kept at that number.")
    else:
        cart[product_id] = qty
    session["cart"] = cart
    return redirect(url_for("view_cart"))


@app.post("/cart/remove")
def remove_from_cart():
    product_id = request.form.get("product_id", "")
    cart = session.get("cart", {})
    cart.pop(product_id, None)
    session["cart"] = cart
    return redirect(url_for("view_cart"))


@app.get("/checkout")
def checkout():
    items, total = cart_lines()
    return render_template("checkout.html", items=items, total=total)


@app.route("/account/new", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("consent.html")
    if request.form.get("consent") != "accept":
        session["consent"] = "declined"
        flash("You declined account data collection. Search and the cart are still available.")
        return redirect(url_for("search"))
    session["consent"] = "accepted"
    return render_template("register.html", categories=categories())


@app.post("/account")
def create_account():
    if session.get("consent") != "accepted":
        flash("Accept the data notice before creating an account.")
        return redirect(url_for("register"))
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    role = request.form.get("role", "shopper")
    preferred = request.form.get("preferred_category", "").strip() or None
    if role not in {"shopper", "seller"}:
        role = "shopper"
    if not name or "@" not in email or len(password) < 8:
        flash("Enter a name, a valid email, and a password of at least 8 characters.")
        return render_template("register.html", categories=categories())
    db = get_db()
    try:
        db.execute(
            """
            INSERT INTO accounts (name, email, password_hash, role, preferred_category)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, email, hash_password(password), role, preferred if role == "shopper" else None),
        )
        db.commit()
    except sqlite3.IntegrityError:
        flash("An account with that email already exists.")
        return render_template("register.html", categories=categories())
    flash("Account created. Sign in to use it.")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        account = get_db().execute("SELECT * FROM accounts WHERE email = ?", (email,)).fetchone()
        if account is None or not check_password(password, account["password_hash"]):
            flash("Email or password does not match.")
        else:
            session["user"] = {
                "id": account["id"],
                "name": account["name"],
                "email": account["email"],
                "role": account["role"],
                "preferred_category": account["preferred_category"],
            }
            flash(f"Signed in as {account['name']}.")
            if account["role"] == "seller":
                return redirect(url_for("seller"))
            return redirect(url_for("search"))
    return render_template("login.html")


@app.post("/logout")
def logout():
    session.pop("user", None)
    flash("Signed out.")
    return redirect(url_for("search"))


@app.get("/seller")
def seller():
    user = session.get("user")
    if not user or user.get("role") != "seller":
        flash("Seller features require a seller account.")
        return redirect(url_for("login"))
    return render_template("seller.html")


# ----- JSON API for Angular (http://localhost:4200) -----

@app.get("/api/health")
def api_health():
    return jsonify({"ok": True, "service": "g49-sprint1"})


@app.get("/api/products")
def api_products():
    keyword = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    use_pref = "q" not in request.args and "category" not in request.args
    products, keyword, category = query_products(keyword, category, use_preference=use_pref)
    return jsonify(
        {
            "products": [product_dict(row) for row in products],
            "categories": categories(),
            "q": keyword,
            "category": category,
            "user": user_dict(session.get("user")),
        }
    )


@app.get("/api/cart")
def api_cart():
    return jsonify(cart_payload())


@app.post("/api/cart/add")
def api_cart_add():
    data = request_data()
    product_id = str(data.get("product_id", ""))
    product = get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None or product["stock"] <= 0:
        return jsonify({"error": "That product is not available.", "cart": cart_payload()}), 400
    cart = session.setdefault("cart", {})
    current = int(cart.get(product_id, 0))
    if current + 1 > product["stock"]:
        return jsonify(
            {
                "error": f"Only {product['stock']} in stock.",
                "cart": cart_payload(),
            }
        ), 400
    cart[product_id] = current + 1
    session["cart"] = cart
    return jsonify({"message": f"Added {product['name']} to the cart.", "cart": cart_payload()})


@app.post("/api/cart/update")
def api_cart_update():
    data = request_data()
    product_id = str(data.get("product_id", ""))
    try:
        qty = int(data.get("qty"))
    except (TypeError, ValueError):
        qty = None
    product = get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    cart = session.get("cart", {})
    message = None
    if product is None or qty is None or qty <= 0:
        cart.pop(product_id, None)
        message = "Item removed from the cart."
    elif qty > product["stock"]:
        cart[product_id] = product["stock"]
        message = f"Only {product['stock']} in stock. The quantity was kept at that number."
    else:
        cart[product_id] = qty
        message = "Cart updated."
    session["cart"] = cart
    return jsonify({"message": message, "cart": cart_payload()})


@app.post("/api/cart/remove")
def api_cart_remove():
    data = request_data()
    product_id = str(data.get("product_id", ""))
    cart = session.get("cart", {})
    cart.pop(product_id, None)
    session["cart"] = cart
    return jsonify({"message": "Item removed from the cart.", "cart": cart_payload()})


@app.post("/api/account/consent")
def api_consent():
    data = request_data()
    consent = str(data.get("consent", "")).strip().lower()
    if consent == "accept":
        session["consent"] = "accepted"
        return jsonify({"accepted": True, "message": "Consent accepted. You can create an account."})
    session["consent"] = "declined"
    return jsonify(
        {
            "accepted": False,
            "message": "Consent declined. Search and the cart are still available.",
        }
    )


@app.post("/api/account")
def api_create_account():
    if session.get("consent") != "accepted":
        return jsonify({"error": "Accept the data notice before creating an account."}), 400
    data = request_data()
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    role = str(data.get("role", "shopper")).strip().lower()
    preferred = str(data.get("preferred_category", "")).strip() or None
    if role not in {"shopper", "seller"}:
        role = "shopper"
    if not name or "@" not in email or len(password) < 8:
        return jsonify(
            {"error": "Enter a name, a valid email, and a password of at least 8 characters."}
        ), 400
    db = get_db()
    try:
        cursor = db.execute(
            """
            INSERT INTO accounts (name, email, password_hash, role, preferred_category)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, email, hash_password(password), role, preferred if role == "shopper" else None),
        )
        db.commit()
        account_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({"error": "An account with that email already exists."}), 409
    return jsonify(
        {
            "message": "Account created. Sign in to use it.",
            "account": {
                "id": account_id,
                "name": name,
                "email": email,
                "role": role,
                "preferred_category": preferred if role == "shopper" else None,
            },
        }
    ), 201


@app.post("/api/login")
def api_login():
    data = request_data()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    account = get_db().execute("SELECT * FROM accounts WHERE email = ?", (email,)).fetchone()
    if account is None or not check_password(password, account["password_hash"]):
        return jsonify({"error": "Email or password does not match."}), 401
    session["user"] = {
        "id": account["id"],
        "name": account["name"],
        "email": account["email"],
        "role": account["role"],
        "preferred_category": account["preferred_category"],
    }
    return jsonify({"message": f"Signed in as {account['name']}.", "user": user_dict(session["user"])})


@app.post("/api/logout")
def api_logout():
    session.pop("user", None)
    return jsonify({"ok": True, "message": "Signed out."})


@app.get("/api/me")
def api_me():
    return jsonify({"user": user_dict(session.get("user")), "consent": session.get("consent")})


@app.get("/api/seller")
def api_seller():
    user = session.get("user")
    if not user or user.get("role") != "seller":
        return jsonify({"error": "Seller features require a seller account."}), 403
    return jsonify({"user": user_dict(user)})


@app.get("/api/seller/listings")
def api_seller_listings():
    user = session.get("user")
    if not user or user.get("role") != "seller":
        return jsonify({"error": "Seller features require a seller account."}), 403
    rows = get_db().execute(
        "SELECT * FROM products WHERE seller_id = ? ORDER BY name", (user["id"],)
    ).fetchall()
    return jsonify({"listings": [product_dict(row) for row in rows]})


@app.post("/api/seller/listings")
def api_seller_add_listing():
    user = session.get("user")
    if not user or user.get("role") != "seller":
        return jsonify({"error": "Seller features require a seller account."}), 403
    data = request_data()
    name = str(data.get("name", "")).strip()
    category = str(data.get("category", "")).strip()
    try:
        price = float(data.get("price"))
        stock = int(data.get("stock"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid price or stock."}), 400
    if not name or not category or price <= 0 or stock < 0:
        return jsonify({"error": "Enter a name, a category, a price above 0, and a whole-number stock."}), 400
    db = get_db()
    cursor = db.execute(
        "INSERT INTO products (name, category, price, stock, seller_id) VALUES (?, ?, ?, ?, ?)",
        (name, category, round(price, 2), stock, user["id"]),
    )
    db.commit()
    row = db.execute("SELECT * FROM products WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify({"listing": product_dict(row)}), 201


@app.delete("/api/seller/listings/<int:product_id>")
def api_seller_remove_listing(product_id):
    user = session.get("user")
    if not user or user.get("role") != "seller":
        return jsonify({"error": "Seller features require a seller account."}), 403
    db = get_db()
    row = db.execute(
        "SELECT id FROM products WHERE id = ? AND seller_id = ?", (product_id, user["id"])
    ).fetchone()
    if row is None:
        return jsonify({"error": "Listing not found."}), 404
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    return jsonify({"ok": True})


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
