"""Sprint 1 prototype: search, cart, account creation, and data consent."""

import hashlib
import os
import secrets
import sqlite3
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

BASE = Path(__file__).resolve().parent

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "g49-sprint1-dev")
app.config["DATABASE"] = os.environ.get("DATABASE", str(BASE / "store.db"))

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


@app.context_processor
def inject_nav():
    cart = session.get("cart", {})
    count = sum(int(qty) for qty in cart.values())
    return {"cart_count": count, "current_user": session.get("user")}


@app.get("/")
def search():
    keyword = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    user = session.get("user") or {}
    if request.args.get("q") is None and request.args.get("category") is None:
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
    products = get_db().execute(sql, params).fetchall()
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


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
