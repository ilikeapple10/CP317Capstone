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
    db.execute("DELETE FROM accounts")
    db.commit()
    db.close()


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


if __name__ == "__main__":
    unittest.main()
