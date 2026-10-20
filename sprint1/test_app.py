"""Checks for the Sprint 1 stories."""

import os
import tempfile
import unittest

DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
DB.close()
os.environ["DATABASE"] = DB.name
os.environ["SECRET_KEY"] = "test"

import app as store  # noqa: E402


class Sprint1Tests(unittest.TestCase):
    def setUp(self):
        store.init_db()
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


if __name__ == "__main__":
    unittest.main()
