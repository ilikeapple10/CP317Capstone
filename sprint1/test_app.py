"""Checks for the Sprint 1 stories and JSON API."""

import os
import tempfile
import unittest

DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
DB.close()
os.environ["DATABASE"] = DB.name
os.environ["SECRET_KEY"] = "test"

import app as store  # noqa: E402


def reset_db():
    store.init_db()
    db = store.connect()
    for table in ("accounts", "products", "orders", "order_items", "wishlist"):
        db.execute(f"DELETE FROM {table}")
    db.commit()
    db.close()
    store.init_db()  # reseeds products with their starting stock


class Sprint1Tests(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.client = store.app.test_client()

    def test_keyword_and_category_search(self):
        keyword = self.client.get("/?q=head")
        self.assertIn(b"Wireless headphones", keyword.data)
        self.assertNotIn(b"Running shoes", keyword.data)

        category = self.client.get("/?q=&category=Apparel")
        self.assertIn(b"Running shoes", category.data)
        self.assertNotIn(b"Wireless headphones", category.data)

    def test_cart_quantity_cap_and_subtotal(self):
        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        with store.app.app_context():
            shoes = store.get_db().execute(
                "SELECT id, price, stock FROM products WHERE name = ?",
                ("Running shoes",),
            ).fetchone()
        self.client.post("/cart/add", data={"product_id": shoes["id"]})
        self.client.post("/cart/update", data={"product_id": shoes["id"], "qty": 99})
        page = self.client.get("/cart")
        self.assertIn(b"Only 4 in stock", page.data)
        self.assertIn(b"$256.00", page.data)
        self.assertIn(b"Proceed to checkout", page.data)

    def test_decline_keeps_search_available(self):
        response = self.client.post("/account/new", data={"consent": "decline"}, follow_redirects=True)
        self.assertIn(b"Search products", response.data)
        self.assertIn(b"declined", response.data)
        with store.app.app_context():
            count = store.get_db().execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        self.assertEqual(count, 0)

    def test_shopper_preference_and_seller_gate(self):
        self.client.post("/account/new", data={"consent": "accept"})
        created = self.client.post(
            "/account",
            data={
                "name": "Avery Shopper",
                "email": "avery@example.com",
                "password": "password1",
                "role": "shopper",
                "preferred_category": "Home",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Sign in", created.data)
        self.client.post(
            "/login",
            data={"email": "avery@example.com", "password": "password1"},
            follow_redirects=True,
        )
        home = self.client.get("/")
        self.assertIn(b"Desk lamp", home.data)
        self.assertNotIn(b"Wireless headphones", home.data)
        blocked = self.client.get("/seller", follow_redirects=True)
        self.assertIn(b"Seller features require a seller account", blocked.data)

        self.client.post("/logout")
        self.client.post("/account/new", data={"consent": "accept"})
        self.client.post(
            "/account",
            data={
                "name": "Riley Seller",
                "email": "riley@example.com",
                "password": "password1",
                "role": "seller",
                "preferred_category": "",
            },
        )
        seller = self.client.post(
            "/login",
            data={"email": "riley@example.com", "password": "password1"},
            follow_redirects=True,
        )
        self.assertIn(b"Seller home", seller.data)


class ApiTests(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.client = store.app.test_client()

    def test_products_json(self):
        response = self.client.get("/api/products?q=head&category=Electronics")
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data["products"]), 1)
        self.assertEqual(data["products"][0]["name"], "Wireless headphones")
        self.assertIn("In stock", data["products"][0]["label"])

    def test_cart_and_consent_flow(self):
        listed = self.client.get("/api/products").get_json()
        headphones = next(p for p in listed["products"] if p["name"] == "Wireless headphones")
        added = self.client.post("/api/cart/add", json={"product_id": headphones["id"]})
        self.assertEqual(added.status_code, 200)
        updated = self.client.post(
            "/api/cart/update",
            json={"product_id": headphones["id"], "qty": 2},
        ).get_json()
        self.assertEqual(updated["cart"]["total"], 78.0)

        declined = self.client.post("/api/account/consent", json={"consent": "decline"}).get_json()
        self.assertFalse(declined["accepted"])
        blocked = self.client.post(
            "/api/account",
            json={
                "name": "No Consent",
                "email": "noconsent@example.com",
                "password": "password1",
                "role": "shopper",
            },
        )
        self.assertEqual(blocked.status_code, 400)

        self.client.post("/api/account/consent", json={"consent": "accept"})
        created = self.client.post(
            "/api/account",
            json={
                "name": "Jordan Shopper",
                "email": "jordan@example.com",
                "password": "password1",
                "role": "shopper",
                "preferred_category": "Home",
            },
        )
        self.assertEqual(created.status_code, 201)
        login = self.client.post(
            "/api/login",
            json={"email": "jordan@example.com", "password": "password1"},
        )
        self.assertEqual(login.status_code, 200)
        prefs = self.client.get("/api/products").get_json()
        names = [p["name"] for p in prefs["products"]]
        self.assertIn("Desk lamp", names)
        self.assertNotIn("Wireless headphones", names)
        seller = self.client.get("/api/seller")
        self.assertEqual(seller.status_code, 403)


PAYMENT = {
    "name": "Guest Buyer",
    "email": "guest@example.com",
    "address": "75 University Ave W, Waterloo",
    "card_number": "4242 4242 4242 4242",
    "expiry": "12/40",
    "cvv": "123",
}


class Sprint2Tests(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.client = store.app.test_client()

    def product(self, name):
        listed = self.client.get("/api/products?q=").get_json()["products"]
        return next(p for p in listed if p["name"] == name)

    def sign_up(self, email, role):
        self.client.post("/api/account/consent", json={"consent": "accept"})
        self.client.post(
            "/api/account",
            json={"name": "Test User", "email": email, "password": "password1", "role": role},
        )
        self.client.post("/api/login", json={"email": email, "password": "password1"})

    def test_guest_checkout_needs_consent_and_valid_payment(self):
        mug = self.product("Coffee mug")
        self.client.post("/api/cart/add", json={"product_id": mug["id"]})

        no_consent = self.client.post("/api/orders", json=PAYMENT)
        self.assertEqual(no_consent.status_code, 400)
        self.assertIn("data notice", no_consent.get_json()["error"])

        self.client.post("/api/account/consent", json={"consent": "accept"})
        bad_card = self.client.post("/api/orders", json={**PAYMENT, "card_number": "1234"})
        self.assertEqual(bad_card.status_code, 400)
        expired = self.client.post("/api/orders", json={**PAYMENT, "expiry": "01/20"})
        self.assertEqual(expired.status_code, 400)

        placed = self.client.post("/api/orders", json=PAYMENT)
        self.assertEqual(placed.status_code, 201)
        order = placed.get_json()["order"]
        self.assertTrue(order["reference"].startswith("G49-"))
        self.assertEqual(self.product("Coffee mug")["stock"], 29)
        with store.app.app_context():
            stored = store.get_db().execute("SELECT * FROM orders").fetchone()
        self.assertNotIn("4242", " ".join(str(v) for v in tuple(stored)))

        found = self.client.post(
            "/api/orders/lookup", json={"order_id": order["id"], "email": "GUEST@example.com"}
        )
        self.assertEqual(found.status_code, 200)
        wrong = self.client.post(
            "/api/orders/lookup", json={"order_id": order["id"], "email": "other@example.com"}
        )
        self.assertEqual(wrong.status_code, 404)

    def test_signed_in_order_shows_in_history(self):
        self.sign_up("shopper@example.com", "shopper")
        lamp = self.product("Desk lamp")
        self.client.post("/api/cart/add", json={"product_id": lamp["id"]})
        self.assertEqual(self.client.post("/api/orders", json=PAYMENT).status_code, 201)
        orders = self.client.get("/api/orders").get_json()["orders"]
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["items"][0]["name"], "Desk lamp")

    def test_listing_with_description_image_and_low_stock_opt_in(self):
        self.sign_up("seller@example.com", "seller")
        listing = {"name": "Ceramic planter", "category": "Home", "price": 18, "stock": 3}
        self.assertEqual(self.client.post("/api/seller/listings", json=listing).status_code, 400)
        bad_image = {**listing, "description": "Glazed pot", "image_url": "planter.jpg"}
        self.assertEqual(self.client.post("/api/seller/listings", json=bad_image).status_code, 400)

        good = {**listing, "description": "Glazed pot", "image_url": "https://example.com/p.jpg"}
        created = self.client.post("/api/seller/listings", json=good)
        self.assertEqual(created.status_code, 201)
        found = self.client.get("/api/products?q=planter").get_json()["products"]
        self.assertEqual(found[0]["description"], "Glazed pot")
        self.assertEqual(found[0]["image_url"], "https://example.com/p.jpg")
        self.assertEqual(found[0]["label"], "Low stock")

        self.assertFalse(self.client.get("/api/seller").get_json()["low_stock_alerts"])
        self.client.post("/api/seller/alerts", json={"enabled": True})
        self.assertTrue(self.client.get("/api/seller").get_json()["low_stock_alerts"])

    def test_wishlist_add_list_remove(self):
        speaker = self.product("Speaker")
        self.assertEqual(
            self.client.post("/api/wishlist", json={"product_id": speaker["id"]}).status_code, 401
        )
        self.sign_up("wish@example.com", "shopper")
        self.client.post("/api/wishlist", json={"product_id": speaker["id"]})
        self.client.post("/api/wishlist", json={"product_id": speaker["id"]})
        items = self.client.get("/api/wishlist").get_json()["items"]
        self.assertEqual([i["name"] for i in items], ["Speaker"])
        self.client.post("/api/logout")
        self.client.post("/api/login", json={"email": "wish@example.com", "password": "password1"})
        self.assertEqual(len(self.client.get("/api/wishlist").get_json()["items"]), 1)
        self.client.delete(f"/api/wishlist/{speaker['id']}")
        self.assertEqual(self.client.get("/api/wishlist").get_json()["items"], [])

    def test_sprint1_orders_table_is_migrated(self):
        db = store.connect()
        db.executescript(
            """
            DROP TABLE orders;
            CREATE TABLE orders (id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL,
                total REAL NOT NULL, placed_at TEXT NOT NULL DEFAULT (datetime('now')));
            INSERT INTO orders (account_id, total) VALUES (1, 9.5);
            """
        )
        db.close()
        store.init_db()
        db = store.connect()
        info = {r["name"]: r["notnull"] for r in db.execute("PRAGMA table_info(orders)")}
        kept = db.execute("SELECT total FROM orders").fetchone()[0]
        db.close()
        self.assertEqual(info["account_id"], 0)
        self.assertIn("reference", info)
        self.assertEqual(kept, 9.5)

    def test_order_rolls_back_when_stock_ran_out(self):
        lamp = self.product("Desk lamp")
        mug = self.product("Coffee mug")
        self.client.post("/api/cart/add", json={"product_id": mug["id"]})
        self.client.post("/api/cart/add", json={"product_id": lamp["id"]})
        db = store.connect()
        db.execute("UPDATE products SET stock = 0 WHERE id = ?", (lamp["id"],))
        db.commit()
        db.close()
        self.client.post("/api/account/consent", json={"consent": "accept"})

        refused = self.client.post("/api/orders", json=PAYMENT)
        self.assertEqual(refused.status_code, 400)
        self.assertIn("Desk lamp", refused.get_json()["error"])
        self.assertEqual(self.product("Coffee mug")["stock"], mug["stock"])
        db = store.connect()
        orders = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        db.close()
        self.assertEqual(orders, 0)

    def test_bad_input_gets_an_error_not_a_crash(self):
        self.assertEqual(self.client.post("/api/orders", json=[1]).status_code, 400)
        self.assertEqual(
            self.client.post("/api/orders/lookup", json={"order_id": [1], "email": "a@b.c"}).status_code,
            404,
        )
        self.client.post("/api/account/consent", json={"consent": "accept"})
        long_year = self.client.post("/api/orders", json={**PAYMENT, "expiry": "12/2099"})
        self.assertIn("expiry", long_year.get_json()["error"])

        self.sign_up("limits@example.com", "seller")
        listing = {"name": "Pot", "category": "Home", "stock": 1, "description": "A pot"}
        for price in ["NaN", "inf", 0.001]:
            response = self.client.post("/api/seller/listings", json={**listing, "price": price})
            self.assertEqual(response.status_code, 400, price)
        too_big = self.client.post("/api/seller/listings", json={**listing, "price": 5, "stock": 10**30})
        self.assertEqual(too_big.status_code, 400)
        self.assertEqual(self.client.delete(f"/api/wishlist/{10**30}").status_code, 400)
        self.client.post("/api/seller/alerts", data={"enabled": "false"})
        self.assertFalse(self.client.get("/api/seller").get_json()["low_stock_alerts"])

    def test_starter_products_get_pictures_without_touching_seller_listings(self):
        self.sign_up("pictures@example.com", "seller")
        listing = {"name": "Coffee mug", "category": "Home", "price": 9, "stock": 2, "description": "Mine"}
        self.client.post("/api/seller/listings", json=listing)
        db = store.connect()
        db.execute("UPDATE products SET image_url = NULL WHERE seller_id IS NULL")
        db.commit()
        db.close()

        store.init_db()

        mugs = self.client.get("/api/products?q=coffee").get_json()["products"]
        self.assertCountEqual(
            [m["image_url"] for m in mugs], ["assets/products/coffee-mug.svg", None]
        )

    def test_keyword_matches_category_and_treats_percent_literally(self):
        found = self.client.get("/api/products?q=electronics").get_json()["products"]
        self.assertEqual({p["name"] for p in found}, {"Wireless headphones", "Speaker"})
        self.assertEqual(self.client.get("/api/products?q=%25").get_json()["products"], [])


if __name__ == "__main__":
    unittest.main()
