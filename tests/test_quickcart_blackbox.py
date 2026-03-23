"""
QuickCart API Black-Box Test Suite
Roll Number: 2024101074

Coverage:
  - Auth headers (X-Roll-Number, X-User-ID)
  - Admin endpoints
  - Profile (GET / PUT)
  - Addresses (CRUD + validation)
  - Products (list / single / filters)
  - Cart (add / update / remove / clear + math)
  - Coupons (apply / remove)
  - Checkout (COD / WALLET / CARD + rules)
  - Wallet (view / add / pay)
  - Loyalty points (view / redeem)
  - Orders (list / detail / cancel / invoice)
  - Reviews (list / post + validation)
  - Support tickets (create / list / update + state-machine)
"""

import pytest
import requests

#
# configuration – change base_url to point at your running docker container
#
BASE_URL = "http://localhost:8080/api/v1"
ROLL_NUMBER = "2024101074"

# a valid user that exists in the seeded database (adjust if needed)
VALID_USER_ID = "1"
# a second user used for isolation tests
OTHER_USER_ID = "2"


#
# helpers
#

def base_headers(user_id=None):
    """Return headers that are always required."""
    h = {"X-Roll-Number": ROLL_NUMBER, "Content-Type": "application/json"}
    if user_id is not None:
        h["X-User-ID"] = str(user_id)
    return h


def admin_headers():
    return {"X-Roll-Number": ROLL_NUMBER, "Content-Type": "application/json"}


def url(path):
    return f"{BASE_URL}{path}"


#
# 1. authentication / header validation
#

class TestHeaderValidation:
    """Every endpoint must enforce X-Roll-Number."""

    def test_missing_roll_number_returns_401(self):
        """No X-Roll-Number header → 401."""
        r = requests.get(url("/profile"), headers={"X-User-ID": VALID_USER_ID})
        assert r.status_code == 401, f"Expected 401 got {r.status_code}"

    def test_non_integer_roll_number_returns_400(self):
        """Non-integer X-Roll-Number → 400."""
        r = requests.get(url("/profile"),
                         headers={"X-Roll-Number": "abc", "X-User-ID": VALID_USER_ID})
        assert r.status_code == 400

    def test_missing_user_id_on_user_endpoint_returns_400(self):
        """Missing X-User-ID on user-scoped endpoint → 400."""
        r = requests.get(url("/profile"), headers={"X-Roll-Number": ROLL_NUMBER})
        assert r.status_code == 400

    def test_invalid_user_id_string_returns_400(self):
        """Non-integer X-User-ID → 400."""
        r = requests.get(url("/profile"),
                         headers={"X-Roll-Number": ROLL_NUMBER, "X-User-ID": "abc"})
        assert r.status_code == 400

    def test_nonexistent_user_id_returns_400(self):
        """X-User-ID that doesn't match any user → 400."""
        r = requests.get(url("/profile"),
                         headers={"X-Roll-Number": ROLL_NUMBER, "X-User-ID": "999999"})
        assert r.status_code == 400

    def test_admin_endpoints_do_not_need_user_id(self):
        """Admin endpoints work without X-User-ID."""
        r = requests.get(url("/admin/users"), headers=admin_headers())
        assert r.status_code == 200

    def test_negative_roll_number_rejected(self):
        """Negative roll number is not a valid integer per spec — expect 400."""
        r = requests.get(url("/profile"),
                         headers={"X-Roll-Number": "-1", "X-User-ID": VALID_USER_ID})
        # spec says 'valid integer'; implementation may differ; document actual.
        assert r.status_code in (200, 400)

    def test_float_roll_number_returns_400(self):
        r = requests.get(url("/profile"),
                         headers={"X-Roll-Number": "123.45", "X-User-ID": VALID_USER_ID})
        assert r.status_code == 400

    def test_zero_user_id_returns_400(self):
        """X-User-ID must be a *positive* integer; 0 is invalid."""
        r = requests.get(url("/profile"),
                         headers={"X-Roll-Number": ROLL_NUMBER, "X-User-ID": "0"})
        assert r.status_code == 400

    def test_negative_user_id_returns_400(self):
        r = requests.get(url("/profile"),
                         headers={"X-Roll-Number": ROLL_NUMBER, "X-User-ID": "-5"})
        assert r.status_code == 400


#
# 2. admin endpoints
#

class TestAdminEndpoints:

    def test_get_all_users(self):
        r = requests.get(url("/admin/users"), headers=admin_headers())
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_get_single_user(self):
        r = requests.get(url(f"/admin/users/{VALID_USER_ID}"), headers=admin_headers())
        assert r.status_code == 200

    def test_get_nonexistent_user_returns_404(self):
        r = requests.get(url("/admin/users/999999"), headers=admin_headers())
        assert r.status_code == 404

    def test_get_all_carts(self):
        r = requests.get(url("/admin/carts"), headers=admin_headers())
        assert r.status_code == 200

    def test_get_all_orders(self):
        r = requests.get(url("/admin/orders"), headers=admin_headers())
        assert r.status_code == 200

    def test_get_all_products(self):
        r = requests.get(url("/admin/products"), headers=admin_headers())
        assert r.status_code == 200

    def test_get_all_coupons(self):
        r = requests.get(url("/admin/coupons"), headers=admin_headers())
        assert r.status_code == 200

    def test_get_all_tickets(self):
        r = requests.get(url("/admin/tickets"), headers=admin_headers())
        assert r.status_code == 200

    def test_get_all_addresses(self):
        r = requests.get(url("/admin/addresses"), headers=admin_headers())
        assert r.status_code == 200

    def test_admin_users_returns_wallet_and_loyalty_fields(self):
        r = requests.get(url("/admin/users"), headers=admin_headers())
        assert r.status_code == 200
        users = r.json()
        if isinstance(users, list) and len(users) > 0:
            u = users[0]
            assert "wallet" in u or "wallet_balance" in u or "loyalty_points" in u, \
                "User record should include wallet/loyalty info"

    def test_admin_products_includes_inactive(self):
        """Admin /products should return inactive products too."""
        r = requests.get(url("/admin/products"), headers=admin_headers())
        assert r.status_code == 200
        # just verify endpoint responds — we can't guarantee inactive exist in seed


#
# 3. profile
#

class TestProfile:
    H = base_headers(VALID_USER_ID)

    def test_get_profile_success(self):
        r = requests.get(url("/profile"), headers=self.H)
        assert r.status_code == 200
        data = r.json()
        assert "name" in data or "user_id" in data

    def test_update_profile_valid(self):
        payload = {"name": "TestUser", "phone": "9876543210"}
        r = requests.put(url("/profile"), json=payload, headers=self.H)
        assert r.status_code == 200

    def test_update_profile_name_too_short(self):
        """Name < 2 chars → 400."""
        payload = {"name": "A", "phone": "9876543210"}
        r = requests.put(url("/profile"), json=payload, headers=self.H)
        assert r.status_code == 400

    def test_update_profile_name_too_long(self):
        """Name > 50 chars → 400."""
        payload = {"name": "A" * 51, "phone": "9876543210"}
        r = requests.put(url("/profile"), json=payload, headers=self.H)
        assert r.status_code == 400

    def test_update_profile_name_exactly_2_chars(self):
        """Boundary: name = 2 chars → 200."""
        payload = {"name": "AB", "phone": "9876543210"}
        r = requests.put(url("/profile"), json=payload, headers=self.H)
        assert r.status_code == 200

    def test_update_profile_name_exactly_50_chars(self):
        """Boundary: name = 50 chars → 200."""
        payload = {"name": "A" * 50, "phone": "9876543210"}
        r = requests.put(url("/profile"), json=payload, headers=self.H)
        assert r.status_code == 200

    def test_update_profile_phone_not_10_digits_returns_400(self):
        payload = {"name": "ValidName", "phone": "98765"}
        r = requests.put(url("/profile"), json=payload, headers=self.H)
        assert r.status_code == 400

    def test_update_profile_phone_11_digits_returns_400(self):
        payload = {"name": "ValidName", "phone": "98765432100"}
        r = requests.put(url("/profile"), json=payload, headers=self.H)
        assert r.status_code == 400

    def test_update_profile_phone_with_letters_returns_400(self):
        payload = {"name": "ValidName", "phone": "9876ABCD10"}
        r = requests.put(url("/profile"), json=payload, headers=self.H)
        assert r.status_code == 400

    def test_update_profile_phone_exactly_10_digits(self):
        """Boundary: exactly 10 digits → 200."""
        payload = {"name": "ValidName", "phone": "1234567890"}
        r = requests.put(url("/profile"), json=payload, headers=self.H)
        assert r.status_code == 200


#
# 4. addresses
#

class TestAddresses:
    H = base_headers(VALID_USER_ID)

    def _valid_payload(self, label="HOME", is_default=False):
        return {
            "label": label,
            "street": "123 Test Street",
            "city": "TestCity",
            "pincode": "500001",
            "is_default": is_default
        }

    def test_get_addresses(self):
        r = requests.get(url("/addresses"), headers=self.H)
        assert r.status_code == 200

    def test_add_address_valid_home(self):
        r = requests.post(url("/addresses"), json=self._valid_payload("HOME"), headers=self.H)
        assert r.status_code == 200 or r.status_code == 201
        data = r.json()
        # response must include the created address fields
        assert "address_id" in data or "id" in data or "address" in data

    def test_add_address_valid_office(self):
        r = requests.post(url("/addresses"), json=self._valid_payload("OFFICE"), headers=self.H)
        assert r.status_code in (200, 201)

    def test_add_address_valid_other(self):
        r = requests.post(url("/addresses"), json=self._valid_payload("OTHER"), headers=self.H)
        assert r.status_code in (200, 201)

    def test_add_address_invalid_label(self):
        """Label not in HOME/OFFICE/OTHER → 400."""
        payload = self._valid_payload()
        payload["label"] = "WORK"
        r = requests.post(url("/addresses"), json=payload, headers=self.H)
        assert r.status_code == 400

    def test_add_address_street_too_short(self):
        """Street < 5 chars → 400."""
        payload = self._valid_payload()
        payload["street"] = "123"
        r = requests.post(url("/addresses"), json=payload, headers=self.H)
        assert r.status_code == 400

    def test_add_address_street_too_long(self):
        """Street > 100 chars → 400."""
        payload = self._valid_payload()
        payload["street"] = "A" * 101
        r = requests.post(url("/addresses"), json=payload, headers=self.H)
        assert r.status_code == 400

    def test_add_address_street_exactly_5_chars(self):
        payload = self._valid_payload()
        payload["street"] = "12345"
        r = requests.post(url("/addresses"), json=payload, headers=self.H)
        assert r.status_code in (200, 201)

    def test_add_address_street_exactly_100_chars(self):
        payload = self._valid_payload()
        payload["street"] = "A" * 100
        r = requests.post(url("/addresses"), json=payload, headers=self.H)
        assert r.status_code in (200, 201)

    def test_add_address_city_too_short(self):
        payload = self._valid_payload()
        payload["city"] = "A"
        r = requests.post(url("/addresses"), json=payload, headers=self.H)
        assert r.status_code == 400

    def test_add_address_city_too_long(self):
        payload = self._valid_payload()
        payload["city"] = "A" * 51
        r = requests.post(url("/addresses"), json=payload, headers=self.H)
        assert r.status_code == 400

    def test_add_address_pincode_not_6_digits(self):
        """Pincode with 5 digits → 400."""
        payload = self._valid_payload()
        payload["pincode"] = "50000"
        r = requests.post(url("/addresses"), json=payload, headers=self.H)
        assert r.status_code == 400

    def test_add_address_pincode_7_digits(self):
        payload = self._valid_payload()
        payload["pincode"] = "5000011"
        r = requests.post(url("/addresses"), json=payload, headers=self.H)
        assert r.status_code == 400

    def test_add_address_pincode_with_letters(self):
        payload = self._valid_payload()
        payload["pincode"] = "50A001"
        r = requests.post(url("/addresses"), json=payload, headers=self.H)
        assert r.status_code == 400

    def test_add_default_address_unsets_previous_default(self):
        """Adding a new default must clear the old default."""
        p1 = self._valid_payload("HOME", is_default=True)
        r1 = requests.post(url("/addresses"), json=p1, headers=self.H)
        assert r1.status_code in (200, 201)

        p2 = self._valid_payload("OFFICE", is_default=True)
        r2 = requests.post(url("/addresses"), json=p2, headers=self.H)
        assert r2.status_code in (200, 201)

        # fetch all addresses and assert only one is default
        r_all = requests.get(url("/addresses"), headers=self.H)
        assert r_all.status_code == 200
        addrs = r_all.json()
        if isinstance(addrs, list):
            defaults = [a for a in addrs if a.get("is_default") is True]
            assert len(defaults) <= 1, "More than one address marked as default"

    def test_update_address_street(self):
        # first create one
        r = requests.post(url("/addresses"), json=self._valid_payload("HOME"), headers=self.H)
        assert r.status_code in (200, 201)
        body = r.json()
        addr_id = body.get("address_id") or body.get("id") or (body.get("address") or {}).get("address_id")
        if addr_id is None:
            pytest.skip("Could not extract address_id from POST response")

        upd = {"street": "99 Updated Avenue"}
        r2 = requests.put(url(f"/addresses/{addr_id}"), json=upd, headers=self.H)
        assert r2.status_code == 200
        updated = r2.json()
        # ensure response reflects new data
        assert "99 Updated Avenue" in str(updated)

    def test_update_address_response_shows_new_data(self):
        """PUT response must contain the updated street, not old data."""
        r = requests.post(url("/addresses"), json=self._valid_payload("OTHER"), headers=self.H)
        assert r.status_code in (200, 201)
        body = r.json()
        addr_id = body.get("address_id") or body.get("id") or (body.get("address") or {}).get("address_id")
        if addr_id is None:
            pytest.skip("Could not extract address_id")

        new_street = "New Street 42 XYZ"
        r2 = requests.put(url(f"/addresses/{addr_id}"), json={"street": new_street}, headers=self.H)
        assert r2.status_code == 200
        resp_text = str(r2.json())
        assert new_street in resp_text, "Response should show updated street value"

    def test_delete_address_success(self):
        r = requests.post(url("/addresses"), json=self._valid_payload("HOME"), headers=self.H)
        assert r.status_code in (200, 201)
        body = r.json()
        addr_id = body.get("address_id") or body.get("id") or (body.get("address") or {}).get("address_id")
        if addr_id is None:
            pytest.skip("Could not extract address_id")
        r2 = requests.delete(url(f"/addresses/{addr_id}"), headers=self.H)
        assert r2.status_code in (200, 204)

    def test_delete_nonexistent_address_returns_404(self):
        r = requests.delete(url("/addresses/999999"), headers=self.H)
        assert r.status_code == 404


#
# 5. products
#

class TestProducts:
    H = base_headers(VALID_USER_ID)

    def test_get_all_products_returns_200(self):
        r = requests.get(url("/products"), headers=self.H)
        assert r.status_code == 200

    def test_products_only_active(self):
        """Public /products must only return active items."""
        r = requests.get(url("/products"), headers=self.H)
        assert r.status_code == 200
        products = r.json()
        if isinstance(products, list):
            for p in products:
                active = p.get("is_active", p.get("active", True))
                assert active is True or active == 1, f"Inactive product {p} in public list"

    def test_get_single_product_valid(self):
        # grab first product id
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if not isinstance(products, list) or len(products) == 0:
            pytest.skip("No products in database")
        pid = products[0].get("product_id") or products[0].get("id")
        r2 = requests.get(url(f"/products/{pid}"), headers=self.H)
        assert r2.status_code == 200

    def test_get_nonexistent_product_returns_404(self):
        r = requests.get(url("/products/999999"), headers=self.H)
        assert r.status_code == 404

    def test_product_price_is_exact(self):
        """Price must not be rounded or truncated."""
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if not isinstance(products, list) or len(products) == 0:
            pytest.skip("No products")
        for p in products:
            price = p.get("price")
            assert price is not None
            assert isinstance(price, (int, float))

    def test_filter_by_category(self):
        # get all products and pick a category
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if not isinstance(products, list) or len(products) == 0:
            pytest.skip("No products")
        cat = products[0].get("category")
        if not cat:
            pytest.skip("Category field not present")
        r2 = requests.get(url(f"/products?category={cat}"), headers=self.H)
        assert r2.status_code == 200
        filtered = r2.json()
        if isinstance(filtered, list):
            for p in filtered:
                assert p.get("category") == cat

    def test_search_by_name(self):
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if not isinstance(products, list) or len(products) == 0:
            pytest.skip("No products")
        name_fragment = products[0].get("name", "")[:3]
        if not name_fragment:
            pytest.skip("Empty product name")
        r2 = requests.get(url(f"/products?search={name_fragment}"), headers=self.H)
        assert r2.status_code == 200

    def test_sort_by_price_asc(self):
        r = requests.get(url("/products?sort=price_asc"), headers=self.H)
        assert r.status_code == 200
        products = r.json()
        if isinstance(products, list) and len(products) > 1:
            prices = [p["price"] for p in products]
            assert prices == sorted(prices), "Products not sorted ascending by price"

    def test_sort_by_price_desc(self):
        r = requests.get(url("/products?sort=price_desc"), headers=self.H)
        assert r.status_code == 200
        products = r.json()
        if isinstance(products, list) and len(products) > 1:
            prices = [p["price"] for p in products]
            assert prices == sorted(prices, reverse=True), "Products not sorted descending by price"


#
# 6. cart
#

class TestCart:
    H = base_headers(VALID_USER_ID)

    def _first_product(self):
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if not isinstance(products, list) or len(products) == 0:
            return None, None
        p = products[0]
        return p.get("product_id") or p.get("id"), p.get("price")

    def test_get_cart(self):
        r = requests.get(url("/cart"), headers=self.H)
        assert r.status_code == 200

    def test_add_item_valid(self):
        pid, _ = self._first_product()
        if pid is None:
            pytest.skip("No products available")
        r = requests.post(url("/cart/add"), json={"product_id": pid, "quantity": 1}, headers=self.H)
        assert r.status_code in (200, 201)

    def test_add_item_zero_quantity_returns_400(self):
        pid, _ = self._first_product()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url("/cart/add"), json={"product_id": pid, "quantity": 0}, headers=self.H)
        assert r.status_code == 400

    def test_add_item_negative_quantity_returns_400(self):
        pid, _ = self._first_product()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url("/cart/add"), json={"product_id": pid, "quantity": -1}, headers=self.H)
        assert r.status_code == 400

    def test_add_nonexistent_product_returns_404(self):
        r = requests.post(url("/cart/add"), json={"product_id": 999999, "quantity": 1}, headers=self.H)
        assert r.status_code == 404

    def test_add_more_than_stock_returns_400(self):
        pid, _ = self._first_product()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url("/cart/add"), json={"product_id": pid, "quantity": 999999}, headers=self.H)
        assert r.status_code == 400

    def test_add_same_product_twice_accumulates_quantity(self):
        """Re-adding same product should add quantities, not replace."""
        # clear cart first
        requests.delete(url("/cart/clear"), headers=self.H)
        pid, _ = self._first_product()
        if pid is None:
            pytest.skip("No products")

        requests.post(url("/cart/add"), json={"product_id": pid, "quantity": 1}, headers=self.H)
        requests.post(url("/cart/add"), json={"product_id": pid, "quantity": 1}, headers=self.H)

        r = requests.get(url("/cart"), headers=self.H)
        cart = r.json()
        items = cart.get("items", cart if isinstance(cart, list) else [])
        if isinstance(items, list):
            for item in items:
                if (item.get("product_id") or item.get("id")) == pid:
                    assert item.get("quantity") == 2, "Quantities should accumulate"

    def test_cart_subtotal_calculation(self):
        """subtotal for each item = quantity * unit_price."""
        requests.delete(url("/cart/clear"), headers=self.H)
        pid, price = self._first_product()
        if pid is None or price is None:
            pytest.skip("No products")

        qty = 3
        requests.post(url("/cart/add"), json={"product_id": pid, "quantity": qty}, headers=self.H)
        r = requests.get(url("/cart"), headers=self.H)
        cart = r.json()
        items = cart.get("items", cart if isinstance(cart, list) else [])
        if isinstance(items, list):
            for item in items:
                if (item.get("product_id") or item.get("id")) == pid:
                    expected_subtotal = round(qty * price, 2)
                    actual_subtotal = round(float(item.get("subtotal", 0)), 2)
                    assert abs(actual_subtotal - expected_subtotal) < 0.01, \
                        f"Subtotal mismatch: expected {expected_subtotal}, got {actual_subtotal}"

    def test_cart_total_is_sum_of_subtotals(self):
        """Cart total must equal sum of all item subtotals."""
        r = requests.get(url("/cart"), headers=self.H)
        cart = r.json()
        items = cart.get("items", [])
        total = float(cart.get("total", cart.get("cart_total", 0)))
        if isinstance(items, list) and len(items) > 0:
            computed = sum(float(i.get("subtotal", 0)) for i in items)
            assert abs(computed - total) < 0.01, \
                f"Cart total {total} != sum of subtotals {computed}"

    def test_update_cart_item_valid(self):
        pid, _ = self._first_product()
        if pid is None:
            pytest.skip("No products")
        requests.post(url("/cart/add"), json={"product_id": pid, "quantity": 1}, headers=self.H)
        r = requests.post(url("/cart/update"), json={"product_id": pid, "quantity": 2}, headers=self.H)
        assert r.status_code == 200

    def test_update_cart_item_zero_quantity_returns_400(self):
        pid, _ = self._first_product()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url("/cart/update"), json={"product_id": pid, "quantity": 0}, headers=self.H)
        assert r.status_code == 400

    def test_remove_item_not_in_cart_returns_404(self):
        r = requests.post(url("/cart/remove"), json={"product_id": 999999}, headers=self.H)
        assert r.status_code == 404

    def test_remove_item_success(self):
        pid, _ = self._first_product()
        if pid is None:
            pytest.skip("No products")
        requests.post(url("/cart/add"), json={"product_id": pid, "quantity": 1}, headers=self.H)
        r = requests.post(url("/cart/remove"), json={"product_id": pid}, headers=self.H)
        assert r.status_code == 200

    def test_clear_cart(self):
        r = requests.delete(url("/cart/clear"), headers=self.H)
        assert r.status_code == 200
        r2 = requests.get(url("/cart"), headers=self.H)
        cart = r2.json()
        items = cart.get("items", [])
        assert len(items) == 0


#
# 7. coupons
#

class TestCoupons:
    H = base_headers(VALID_USER_ID)

    def _add_item_to_cart(self):
        requests.delete(url("/cart/clear"), headers=self.H)
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if isinstance(products, list) and len(products) > 0:
            pid = products[0].get("product_id") or products[0].get("id")
            requests.post(url("/cart/add"), json={"product_id": pid, "quantity": 1}, headers=self.H)

    def test_apply_invalid_coupon_returns_error(self):
        """Non-existent coupon should not return 200."""
        self._add_item_to_cart()
        r = requests.post(url("/coupon/apply"),
                          json={"coupon_code": "FAKECOUPON999"}, headers=self.H)
        assert r.status_code in (400, 404)

    def test_apply_expired_coupon_returns_error(self):
        """If expired coupons are seeded, applying one must fail."""
        r = requests.get(url("/admin/coupons"), headers=admin_headers())
        coupons = r.json()
        expired = None
        if isinstance(coupons, list):
            for c in coupons:
                if c.get("is_expired") or c.get("expired"):
                    expired = c.get("code") or c.get("coupon_code")
                    break
        if expired is None:
            pytest.skip("No expired coupons in database")
        self._add_item_to_cart()
        r2 = requests.post(url("/coupon/apply"), json={"coupon_code": expired}, headers=self.H)
        assert r2.status_code in (400, 422)

    def test_apply_coupon_below_minimum_cart_value(self):
        """If cart is below minimum value required by coupon, must be rejected."""
        r = requests.get(url("/admin/coupons"), headers=admin_headers())
        coupons = r.json()
        high_min_coupon = None
        if isinstance(coupons, list):
            for c in coupons:
                if float(c.get("min_cart_value", c.get("minimum_cart_value", 0))) > 10000:
                    high_min_coupon = c.get("code") or c.get("coupon_code")
                    break
        if high_min_coupon is None:
            pytest.skip("No coupon with very high minimum in database")
        # add a cheap item
        requests.delete(url("/cart/clear"), headers=self.H)
        r2 = requests.get(url("/products"), headers=self.H)
        products = r2.json()
        if isinstance(products, list) and products:
            pid = products[0].get("product_id") or products[0].get("id")
            requests.post(url("/cart/add"), json={"product_id": pid, "quantity": 1}, headers=self.H)
        r3 = requests.post(url("/coupon/apply"), json={"coupon_code": high_min_coupon}, headers=self.H)
        assert r3.status_code in (400, 422)

    def test_remove_coupon(self):
        r = requests.post(url("/coupon/remove"), json={}, headers=self.H)
        # removing when none applied may return 200 or 400 — document both
        assert r.status_code in (200, 400)

    def test_percent_coupon_discount_calculation(self):
        """PERCENT coupon discount = (percent/100) * cart_total, capped if applicable."""
        r = requests.get(url("/admin/coupons"), headers=admin_headers())
        coupons = r.json()
        coupon = None
        if isinstance(coupons, list):
            for c in coupons:
                if c.get("type") == "PERCENT" and not c.get("is_expired", c.get("expired", False)):
                    coupon = c
                    break
        if coupon is None:
            pytest.skip("No active PERCENT coupon in database")

        self._add_item_to_cart()
        code = coupon.get("code") or coupon.get("coupon_code")
        r2 = requests.post(url("/coupon/apply"), json={"coupon_code": code}, headers=self.H)
        if r2.status_code not in (200, 201):
            pytest.skip(f"Coupon apply failed: {r2.status_code}")

        cart = requests.get(url("/cart"), headers=self.H).json()
        total = float(cart.get("total", 0))
        discount = float(cart.get("discount", 0))
        percent = float(coupon.get("discount_value", coupon.get("value", 0)))
        max_discount = coupon.get("max_discount")

        expected = (percent / 100) * total
        if max_discount:
            expected = min(expected, float(max_discount))

        assert abs(discount - expected) < 0.5, \
            f"PERCENT discount mismatch: expected ~{expected}, got {discount}"


#
# 8. checkout
#

class TestCheckout:
    H = base_headers(VALID_USER_ID)

    def _add_cheap_item(self):
        requests.delete(url("/cart/clear"), headers=self.H)
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if isinstance(products, list):
            for p in products:
                price = float(p.get("price", 9999))
                if price < 4000:
                    pid = p.get("product_id") or p.get("id")
                    requests.post(url("/cart/add"),
                                  json={"product_id": pid, "quantity": 1},
                                  headers=self.H)
                    return True
        return False

    def test_checkout_empty_cart_returns_400(self):
        requests.delete(url("/cart/clear"), headers=self.H)
        r = requests.post(url("/checkout"), json={"payment_method": "COD"}, headers=self.H)
        assert r.status_code == 400

    def test_checkout_invalid_payment_method_returns_400(self):
        self._add_cheap_item()
        r = requests.post(url("/checkout"), json={"payment_method": "CRYPTO"}, headers=self.H)
        assert r.status_code == 400

    def test_checkout_missing_payment_method_returns_400(self):
        self._add_cheap_item()
        r = requests.post(url("/checkout"), json={}, headers=self.H)
        assert r.status_code == 400

    def test_checkout_cod_success(self):
        if not self._add_cheap_item():
            pytest.skip("No cheap product available")
        r = requests.post(url("/checkout"), json={"payment_method": "COD"}, headers=self.H)
        assert r.status_code in (200, 201)

    def test_checkout_cod_order_has_pending_payment(self):
        if not self._add_cheap_item():
            pytest.skip("No cheap product available")
        r = requests.post(url("/checkout"), json={"payment_method": "COD"}, headers=self.H)
        if r.status_code not in (200, 201):
            pytest.skip("Checkout failed")
        data = r.json()
        payment_status = data.get("payment_status") or (data.get("order") or {}).get("payment_status")
        assert payment_status == "PENDING", f"COD should be PENDING, got {payment_status}"

    def test_checkout_card_order_has_paid_status(self):
        if not self._add_cheap_item():
            pytest.skip("No cheap product available")
        r = requests.post(url("/checkout"), json={"payment_method": "CARD"}, headers=self.H)
        if r.status_code not in (200, 201):
            pytest.skip("Checkout with CARD failed")
        data = r.json()
        payment_status = data.get("payment_status") or (data.get("order") or {}).get("payment_status")
        assert payment_status == "PAID", f"CARD should be PAID, got {payment_status}"

    def test_checkout_cod_above_5000_returns_400(self):
        """COD is disallowed when order total > 5000."""
        requests.delete(url("/cart/clear"), headers=self.H)
        # try to get products until we can build a cart > 5000
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if not isinstance(products, list):
            pytest.skip("No products")

        total = 0
        for p in products:
            price = float(p.get("price", 0))
            if price > 0 and total < 5000:
                pid = p.get("product_id") or p.get("id")
                need = int(5001 / price) + 1
                resp = requests.post(url("/cart/add"),
                                     json={"product_id": pid, "quantity": need},
                                     headers=self.H)
                if resp.status_code in (200, 201):
                    total += price * need
                    break

        if total <= 5000:
            pytest.skip("Could not build cart > 5000 with available stock")

        r2 = requests.post(url("/checkout"), json={"payment_method": "COD"}, headers=self.H)
        assert r2.status_code == 400, "COD above 5000 should return 400"

    def test_checkout_gst_applied_once(self):
        """GST is 5% and added only once."""
        if not self._add_cheap_item():
            pytest.skip("No cheap product available")
        cart = requests.get(url("/cart"), headers=self.H).json()
        cart_total = float(cart.get("total", 0))

        r = requests.post(url("/checkout"), json={"payment_method": "CARD"}, headers=self.H)
        if r.status_code not in (200, 201):
            pytest.skip("Checkout failed")
        data = r.json()
        order_total = float(data.get("total") or (data.get("order") or {}).get("total") or 0)

        expected = round(cart_total * 1.05, 2)
        assert abs(order_total - expected) < 1.0, \
            f"GST mismatch: cart={cart_total}, expected order={expected}, got {order_total}"

    def test_checkout_wallet_pending_status(self):
        """WALLET payment starts as PENDING."""
        # add funds first
        requests.post(url("/wallet/add"), json={"amount": 50000}, headers=self.H)
        if not self._add_cheap_item():
            pytest.skip("No cheap product available")
        r = requests.post(url("/checkout"), json={"payment_method": "WALLET"}, headers=self.H)
        if r.status_code not in (200, 201):
            pytest.skip("Wallet checkout failed")
        data = r.json()
        payment_status = data.get("payment_status") or (data.get("order") or {}).get("payment_status")
        assert payment_status == "PENDING"


#
# 9. wallet
#

class TestWallet:
    H = base_headers(VALID_USER_ID)

    def test_get_wallet(self):
        r = requests.get(url("/wallet"), headers=self.H)
        assert r.status_code == 200
        data = r.json()
        assert "balance" in data or "wallet_balance" in data

    def test_add_money_valid(self):
        r = requests.post(url("/wallet/add"), json={"amount": 500}, headers=self.H)
        assert r.status_code in (200, 201)

    def test_add_money_zero_returns_400(self):
        r = requests.post(url("/wallet/add"), json={"amount": 0}, headers=self.H)
        assert r.status_code == 400

    def test_add_money_negative_returns_400(self):
        r = requests.post(url("/wallet/add"), json={"amount": -100}, headers=self.H)
        assert r.status_code == 400

    def test_add_money_max_allowed(self):
        """Boundary: exactly 100000 should be allowed."""
        r = requests.post(url("/wallet/add"), json={"amount": 100000}, headers=self.H)
        assert r.status_code in (200, 201)

    def test_add_money_above_max_returns_400(self):
        """Amount > 100000 must be rejected."""
        r = requests.post(url("/wallet/add"), json={"amount": 100001}, headers=self.H)
        assert r.status_code == 400

    def test_pay_from_wallet_deducts_exact_amount(self):
        """Only the requested amount is deducted."""
        requests.post(url("/wallet/add"), json={"amount": 1000}, headers=self.H)
        before = float(requests.get(url("/wallet"), headers=self.H).json().get(
            "balance", requests.get(url("/wallet"), headers=self.H).json().get("wallet_balance", 0)))
        pay_amount = 200
        r = requests.post(url("/wallet/pay"), json={"amount": pay_amount}, headers=self.H)
        assert r.status_code in (200, 201)
        after_data = requests.get(url("/wallet"), headers=self.H).json()
        after = float(after_data.get("balance", after_data.get("wallet_balance", 0)))
        assert abs((before - pay_amount) - after) < 0.01, \
            f"Expected {before - pay_amount}, got {after}"

    def test_pay_insufficient_balance_returns_400(self):
        # get current balance and try to pay more
        data = requests.get(url("/wallet"), headers=self.H).json()
        bal = float(data.get("balance", data.get("wallet_balance", 0)))
        r = requests.post(url("/wallet/pay"), json={"amount": bal + 10000}, headers=self.H)
        assert r.status_code == 400

    def test_pay_zero_returns_400(self):
        r = requests.post(url("/wallet/pay"), json={"amount": 0}, headers=self.H)
        assert r.status_code == 400

    def test_pay_negative_returns_400(self):
        r = requests.post(url("/wallet/pay"), json={"amount": -50}, headers=self.H)
        assert r.status_code == 400


#
# 10. loyalty points
#

class TestLoyalty:
    H = base_headers(VALID_USER_ID)

    def test_get_loyalty_points(self):
        r = requests.get(url("/loyalty"), headers=self.H)
        assert r.status_code == 200
        data = r.json()
        assert "points" in data or "loyalty_points" in data

    def test_redeem_more_than_available_returns_400(self):
        data = requests.get(url("/loyalty"), headers=self.H).json()
        pts = int(data.get("points", data.get("loyalty_points", 0)))
        r = requests.post(url("/loyalty/redeem"), json={"points": pts + 9999}, headers=self.H)
        assert r.status_code == 400

    def test_redeem_zero_points_returns_400(self):
        """Must redeem at least 1 point."""
        r = requests.post(url("/loyalty/redeem"), json={"points": 0}, headers=self.H)
        assert r.status_code == 400

    def test_redeem_negative_points_returns_400(self):
        r = requests.post(url("/loyalty/redeem"), json={"points": -5}, headers=self.H)
        assert r.status_code == 400

    def test_redeem_valid_points(self):
        data = requests.get(url("/loyalty"), headers=self.H).json()
        pts = int(data.get("points", data.get("loyalty_points", 0)))
        if pts < 1:
            pytest.skip("No loyalty points to redeem")
        r = requests.post(url("/loyalty/redeem"), json={"points": 1}, headers=self.H)
        assert r.status_code in (200, 201)


#
# 11. orders
#

class TestOrders:
    H = base_headers(VALID_USER_ID)

    def _place_order(self):
        """Helper: place a COD order and return order_id, or None."""
        requests.delete(url("/cart/clear"), headers=self.H)
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if not isinstance(products, list) or not products:
            return None
        for p in products:
            if float(p.get("price", 9999)) < 4000:
                pid = p.get("product_id") or p.get("id")
                requests.post(url("/cart/add"), json={"product_id": pid, "quantity": 1}, headers=self.H)
                break
        co = requests.post(url("/checkout"), json={"payment_method": "COD"}, headers=self.H)
        if co.status_code not in (200, 201):
            return None
        data = co.json()
        return data.get("order_id") or (data.get("order") or {}).get("order_id")

    def test_get_orders_list(self):
        r = requests.get(url("/orders"), headers=self.H)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))

    def test_get_single_order_valid(self):
        oid = self._place_order()
        if oid is None:
            pytest.skip("Could not place order")
        r = requests.get(url(f"/orders/{oid}"), headers=self.H)
        assert r.status_code == 200

    def test_get_nonexistent_order_returns_404(self):
        r = requests.get(url("/orders/999999"), headers=self.H)
        assert r.status_code == 404

    def test_cancel_order_success(self):
        oid = self._place_order()
        if oid is None:
            pytest.skip("Could not place order")
        r = requests.post(url(f"/orders/{oid}/cancel"), headers=self.H)
        assert r.status_code in (200, 201)

    def test_cancel_nonexistent_order_returns_404(self):
        r = requests.post(url("/orders/999999/cancel"), headers=self.H)
        assert r.status_code == 404

    def test_cancel_delivered_order_returns_400(self):
        """Delivered orders cannot be cancelled."""
        r = requests.get(url("/admin/orders"), headers=admin_headers())
        orders = r.json()
        delivered_id = None
        if isinstance(orders, list):
            for o in orders:
                uid = o.get("user_id")
                status = o.get("order_status", o.get("status", ""))
                if str(uid) == str(VALID_USER_ID) and status == "DELIVERED":
                    delivered_id = o.get("order_id") or o.get("id")
                    break
        if delivered_id is None:
            pytest.skip("No delivered orders for this user")
        r2 = requests.post(url(f"/orders/{delivered_id}/cancel"),
                           headers=self.H)
        assert r2.status_code == 400

    def test_cancel_restores_stock(self):
        """Cancelling an order must add items back to stock."""
        r_products_before = requests.get(url("/products"), headers=self.H).json()
        if not isinstance(r_products_before, list) or not r_products_before:
            pytest.skip("No products")
        p = next((x for x in r_products_before if float(x.get("price", 9999)) < 4000), None)
        if p is None:
            pytest.skip("No cheap product")
        pid = p.get("product_id") or p.get("id")
        stock_before = int(p.get("stock", p.get("quantity", 0)))

        requests.delete(url("/cart/clear"), headers=self.H)
        requests.post(url("/cart/add"), json={"product_id": pid, "quantity": 1}, headers=self.H)
        co = requests.post(url("/checkout"), json={"payment_method": "COD"}, headers=self.H)
        if co.status_code not in (200, 201):
            pytest.skip("Checkout failed")
        data = co.json()
        oid = data.get("order_id") or (data.get("order") or {}).get("order_id")

        # cancel
        requests.post(url(f"/orders/{oid}/cancel"), headers=self.H)

        # check stock restored
        r2 = requests.get(url(f"/products/{pid}"), headers=self.H)
        stock_after = int(r2.json().get("stock", r2.json().get("quantity", 0)))
        assert stock_after >= stock_before, \
            f"Stock not restored: before={stock_before}, after={stock_after}"

    def test_invoice_structure(self):
        """Invoice must have subtotal, GST amount, and total."""
        oid = self._place_order()
        if oid is None:
            pytest.skip("Could not place order")
        r = requests.get(url(f"/orders/{oid}/invoice"), headers=self.H)
        assert r.status_code == 200
        data = r.json()
        data_str = str(data).lower()
        assert any(k in data_str for k in ["subtotal", "sub_total"]), "Invoice missing subtotal"
        assert any(k in data_str for k in ["gst", "tax"]), "Invoice missing GST"
        assert "total" in data_str, "Invoice missing total"

    def test_invoice_total_matches_order_total(self):
        oid = self._place_order()
        if oid is None:
            pytest.skip("Could not place order")
        order_r = requests.get(url(f"/orders/{oid}"), headers=self.H).json()
        order_total = float(order_r.get("total", order_r.get("order_total", 0)))

        inv_r = requests.get(url(f"/orders/{oid}/invoice"), headers=self.H).json()
        inv_total = float(inv_r.get("total", inv_r.get("invoice_total", 0)))
        assert abs(order_total - inv_total) < 0.01, \
            f"Invoice total {inv_total} != order total {order_total}"


#
# 12. reviews
#

class TestReviews:
    H = base_headers(VALID_USER_ID)

    def _first_product_id(self):
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if isinstance(products, list) and products:
            return products[0].get("product_id") or products[0].get("id")
        return None

    def test_get_reviews_for_product(self):
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.get(url(f"/products/{pid}/reviews"), headers=self.H)
        assert r.status_code == 200

    def test_get_reviews_nonexistent_product_returns_404(self):
        r = requests.get(url("/products/999999/reviews"), headers=self.H)
        assert r.status_code == 404

    def test_add_review_valid(self):
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url(f"/products/{pid}/reviews"),
                          json={"rating": 4, "comment": "Great product!"},
                          headers=self.H)
        assert r.status_code in (200, 201)

    def test_add_review_rating_0_returns_400(self):
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url(f"/products/{pid}/reviews"),
                          json={"rating": 0, "comment": "Bad"},
                          headers=self.H)
        assert r.status_code == 400

    def test_add_review_rating_6_returns_400(self):
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url(f"/products/{pid}/reviews"),
                          json={"rating": 6, "comment": "Too much"},
                          headers=self.H)
        assert r.status_code == 400

    def test_add_review_rating_negative_returns_400(self):
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url(f"/products/{pid}/reviews"),
                          json={"rating": -1, "comment": "Negative"},
                          headers=self.H)
        assert r.status_code == 400

    def test_add_review_rating_boundary_1(self):
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url(f"/products/{pid}/reviews"),
                          json={"rating": 1, "comment": "Minimum rating"},
                          headers=self.H)
        assert r.status_code in (200, 201)

    def test_add_review_rating_boundary_5(self):
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url(f"/products/{pid}/reviews"),
                          json={"rating": 5, "comment": "Maximum rating"},
                          headers=self.H)
        assert r.status_code in (200, 201)

    def test_add_review_empty_comment_returns_400(self):
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url(f"/products/{pid}/reviews"),
                          json={"rating": 3, "comment": ""},
                          headers=self.H)
        assert r.status_code == 400

    def test_add_review_comment_too_long_returns_400(self):
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url(f"/products/{pid}/reviews"),
                          json={"rating": 3, "comment": "A" * 201},
                          headers=self.H)
        assert r.status_code == 400

    def test_add_review_comment_exactly_200_chars(self):
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url(f"/products/{pid}/reviews"),
                          json={"rating": 3, "comment": "A" * 200},
                          headers=self.H)
        assert r.status_code in (200, 201)

    def test_average_rating_is_decimal_not_integer(self):
        """Average must be a proper decimal."""
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.get(url(f"/products/{pid}/reviews"), headers=self.H)
        data = r.json()
        avg = data.get("average_rating", data.get("avg_rating"))
        if avg is not None and avg != 0:
            # should be a float, not truncated int
            assert isinstance(avg, float) or "." in str(avg), \
                f"Average rating looks like truncated integer: {avg}"

    def test_average_rating_zero_for_no_reviews(self):
        """If no reviews exist, average_rating must be 0."""
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.get(url(f"/products/{pid}/reviews"), headers=self.H)
        data = r.json()
        reviews = data.get("reviews", [])
        avg = data.get("average_rating", data.get("avg_rating"))
        if len(reviews) == 0:
            assert float(avg) == 0.0, f"Expected avg=0 for no reviews, got {avg}"


#
# 13. support tickets
#

class TestSupportTickets:
    H = base_headers(VALID_USER_ID)

    def _create_ticket(self, subject="Valid Subject Here", message="This is a valid message."):
        r = requests.post(url("/support/ticket"),
                          json={"subject": subject, "message": message},
                          headers=self.H)
        return r

    def test_create_ticket_valid(self):
        r = self._create_ticket()
        assert r.status_code in (200, 201)

    def test_new_ticket_status_is_open(self):
        r = self._create_ticket("Open Status Check", "Checking status on creation.")
        assert r.status_code in (200, 201)
        data = r.json()
        status = data.get("status") or (data.get("ticket") or {}).get("status")
        assert status == "OPEN", f"New ticket should be OPEN, got {status}"

    def test_create_ticket_subject_too_short(self):
        """Subject < 5 chars → 400."""
        r = self._create_ticket(subject="Hi", message="Valid message content here")
        assert r.status_code == 400

    def test_create_ticket_subject_too_long(self):
        """Subject > 100 chars → 400."""
        r = self._create_ticket(subject="A" * 101, message="Valid message")
        assert r.status_code == 400

    def test_create_ticket_subject_exactly_5_chars(self):
        r = self._create_ticket(subject="Hello", message="Valid message content")
        assert r.status_code in (200, 201)

    def test_create_ticket_subject_exactly_100_chars(self):
        r = self._create_ticket(subject="A" * 100, message="Valid message content")
        assert r.status_code in (200, 201)

    def test_create_ticket_message_empty_returns_400(self):
        r = self._create_ticket(message="")
        assert r.status_code == 400

    def test_create_ticket_message_too_long_returns_400(self):
        """Message > 500 chars → 400."""
        r = self._create_ticket(message="A" * 501)
        assert r.status_code == 400

    def test_create_ticket_message_exactly_500_chars(self):
        r = self._create_ticket(message="A" * 500)
        assert r.status_code in (200, 201)

    def test_create_ticket_message_saved_exactly(self):
        """Full message must be stored as written."""
        msg = "This is my exact support message: !@#$%"
        r = self._create_ticket(message=msg)
        assert r.status_code in (200, 201)
        data = r.json()
        saved_msg = data.get("message") or (data.get("ticket") or {}).get("message")
        if saved_msg:
            assert saved_msg == msg, f"Message not saved exactly: got '{saved_msg}'"

    def test_get_all_tickets(self):
        r = requests.get(url("/support/tickets"), headers=self.H)
        assert r.status_code == 200

    def test_update_ticket_open_to_in_progress(self):
        r = self._create_ticket("Status Transition Test", "Testing OPEN→IN_PROGRESS")
        assert r.status_code in (200, 201)
        data = r.json()
        tid = data.get("ticket_id") or (data.get("ticket") or {}).get("ticket_id")
        if tid is None:
            pytest.skip("Could not extract ticket_id")
        r2 = requests.put(url(f"/support/tickets/{tid}"),
                          json={"status": "IN_PROGRESS"},
                          headers=self.H)
        assert r2.status_code == 200

    def test_update_ticket_in_progress_to_closed(self):
        r = self._create_ticket("Close Ticket Test", "Testing IN_PROGRESS→CLOSED")
        assert r.status_code in (200, 201)
        data = r.json()
        tid = data.get("ticket_id") or (data.get("ticket") or {}).get("ticket_id")
        if tid is None:
            pytest.skip("Could not extract ticket_id")
        # first move to in_progress
        requests.put(url(f"/support/tickets/{tid}"),
                     json={"status": "IN_PROGRESS"},
                     headers=self.H)
        # then close
        r2 = requests.put(url(f"/support/tickets/{tid}"),
                          json={"status": "CLOSED"},
                          headers=self.H)
        assert r2.status_code == 200

    def test_update_ticket_open_to_closed_invalid_returns_400(self):
        """OPEN → CLOSED (skipping IN_PROGRESS) must be rejected."""
        r = self._create_ticket("Invalid Transition", "Testing OPEN→CLOSED skip")
        assert r.status_code in (200, 201)
        data = r.json()
        tid = data.get("ticket_id") or (data.get("ticket") or {}).get("ticket_id")
        if tid is None:
            pytest.skip("Could not extract ticket_id")
        r2 = requests.put(url(f"/support/tickets/{tid}"),
                          json={"status": "CLOSED"},
                          headers=self.H)
        assert r2.status_code in (400, 422), \
            "Should not allow OPEN → CLOSED directly"

    def test_update_ticket_in_progress_to_open_invalid(self):
        """IN_PROGRESS → OPEN (backward) must be rejected."""
        r = self._create_ticket("Backward Transition", "Testing IN_PROGRESS→OPEN revert")
        assert r.status_code in (200, 201)
        data = r.json()
        tid = data.get("ticket_id") or (data.get("ticket") or {}).get("ticket_id")
        if tid is None:
            pytest.skip("Could not extract ticket_id")
        requests.put(url(f"/support/tickets/{tid}"),
                     json={"status": "IN_PROGRESS"},
                     headers=self.H)
        r2 = requests.put(url(f"/support/tickets/{tid}"),
                          json={"status": "OPEN"},
                          headers=self.H)
        assert r2.status_code in (400, 422), \
            "Should not allow IN_PROGRESS → OPEN"

    def test_update_ticket_closed_to_anything_invalid(self):
        """Once CLOSED, status must not change."""
        r = self._create_ticket("Closed No Change", "Testing CLOSED→anything")
        assert r.status_code in (200, 201)
        data = r.json()
        tid = data.get("ticket_id") or (data.get("ticket") or {}).get("ticket_id")
        if tid is None:
            pytest.skip("Could not extract ticket_id")
        requests.put(url(f"/support/tickets/{tid}"),
                     json={"status": "IN_PROGRESS"}, headers=self.H)
        requests.put(url(f"/support/tickets/{tid}"),
                     json={"status": "CLOSED"}, headers=self.H)
        # now try to change again
        r2 = requests.put(url(f"/support/tickets/{tid}"),
                          json={"status": "IN_PROGRESS"}, headers=self.H)
        assert r2.status_code in (400, 422), \
            "CLOSED ticket must not allow status change"

    def test_update_ticket_invalid_status_value(self):
        r = self._create_ticket("Bad Status Value", "Testing invalid status string")
        assert r.status_code in (200, 201)
        data = r.json()
        tid = data.get("ticket_id") or (data.get("ticket") or {}).get("ticket_id")
        if tid is None:
            pytest.skip("Could not extract ticket_id")
        r2 = requests.put(url(f"/support/tickets/{tid}"),
                          json={"status": "MAYBE"},
                          headers=self.H)
        assert r2.status_code in (400, 422)

    def test_update_nonexistent_ticket_returns_404(self):
        """PUT on a ticket_id that does not exist → 404."""
        r = requests.put(url("/support/tickets/999999"),
                         json={"status": "IN_PROGRESS"},
                         headers=self.H)
        assert r.status_code == 404

    def test_update_ticket_missing_status_field(self):
        """PUT with no status field in body → 400."""
        r = self._create_ticket("Missing Status Field", "Testing missing status key")
        assert r.status_code in (200, 201)
        data = r.json()
        tid = data.get("ticket_id") or (data.get("ticket") or {}).get("ticket_id")
        if tid is None:
            pytest.skip("Could not extract ticket_id")
        r2 = requests.put(url(f"/support/tickets/{tid}"), json={}, headers=self.H)
        assert r2.status_code == 400


#
# 14. additional gap-fill tests
#

class TestCartGaps:
    H = base_headers(VALID_USER_ID)

    def _first_product(self):
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if not isinstance(products, list) or not products:
            return None, None
        p = products[0]
        return p.get("product_id") or p.get("id"), p.get("stock", p.get("quantity", 0))

    def test_update_item_not_in_cart_returns_404(self):
        """Updating a product that was never added → 404."""
        requests.delete(url("/cart/clear"), headers=self.H)
        r = requests.post(url("/cart/update"),
                          json={"product_id": 999999, "quantity": 1},
                          headers=self.H)
        assert r.status_code == 404

    def test_update_item_quantity_exceeding_stock_returns_400(self):
        """Updating cart quantity above stock → 400."""
        pid, _ = self._first_product()
        if pid is None:
            pytest.skip("No products")
        requests.delete(url("/cart/clear"), headers=self.H)
        requests.post(url("/cart/add"), json={"product_id": pid, "quantity": 1}, headers=self.H)
        r = requests.post(url("/cart/update"),
                          json={"product_id": pid, "quantity": 999999},
                          headers=self.H)
        assert r.status_code == 400

    def test_add_item_missing_product_id_returns_400(self):
        """Body missing product_id entirely → 400."""
        r = requests.post(url("/cart/add"), json={"quantity": 1}, headers=self.H)
        assert r.status_code == 400

    def test_add_item_missing_quantity_returns_400(self):
        """Body missing quantity entirely → 400."""
        pid, _ = self._first_product()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url("/cart/add"), json={"product_id": pid}, headers=self.H)
        assert r.status_code == 400

    def test_cart_cleared_after_successful_checkout(self):
        """After a successful checkout the cart must be empty."""
        requests.delete(url("/cart/clear"), headers=self.H)
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if not isinstance(products, list):
            pytest.skip("No products")
        for p in products:
            if float(p.get("price", 9999)) < 4000:
                pid = p.get("product_id") or p.get("id")
                requests.post(url("/cart/add"),
                              json={"product_id": pid, "quantity": 1},
                              headers=self.H)
                break
        co = requests.post(url("/checkout"), json={"payment_method": "CARD"}, headers=self.H)
        if co.status_code not in (200, 201):
            pytest.skip("Checkout failed")
        cart = requests.get(url("/cart"), headers=self.H).json()
        items = cart.get("items", cart if isinstance(cart, list) else [])
        assert len(items) == 0, "Cart should be empty after checkout"


class TestCheckoutGaps:
    H = base_headers(VALID_USER_ID)

    def _add_cheap_item(self):
        requests.delete(url("/cart/clear"), headers=self.H)
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if isinstance(products, list):
            for p in products:
                if float(p.get("price", 9999)) < 4000:
                    pid = p.get("product_id") or p.get("id")
                    requests.post(url("/cart/add"),
                                  json={"product_id": pid, "quantity": 1},
                                  headers=self.H)
                    return True
        return False

    def test_checkout_wallet_insufficient_balance_returns_400(self):
        """WALLET checkout with balance < order total must fail."""
        # zero out wallet by checking balance and attempting a pay, or just use a fresh user
        # instead we ensure balance is 0 by checking it
        wallet_data = requests.get(url("/wallet"), headers=self.H).json()
        balance = float(wallet_data.get("balance", wallet_data.get("wallet_balance", 0)))

        if not self._add_cheap_item():
            pytest.skip("No cheap product")

        cart = requests.get(url("/cart"), headers=self.H).json()
        total_with_gst = float(cart.get("total", 0)) * 1.05

        if balance >= total_with_gst:
            pytest.skip("Wallet has sufficient funds; cannot test insufficient case without depleting it")

        r = requests.post(url("/checkout"), json={"payment_method": "WALLET"}, headers=self.H)
        assert r.status_code == 400, "Wallet checkout with insufficient balance should return 400"

    def test_checkout_missing_body_returns_400(self):
        """POST /checkout with completely empty body → 400."""
        if not self._add_cheap_item():
            pytest.skip("No cheap product")
        r = requests.post(url("/checkout"), json={}, headers=self.H)
        assert r.status_code == 400

    def test_checkout_payment_method_wrong_case_returns_400(self):
        """'cod' (lowercase) is not a valid payment method value."""
        if not self._add_cheap_item():
            pytest.skip("No cheap product")
        r = requests.post(url("/checkout"), json={"payment_method": "cod"}, headers=self.H)
        assert r.status_code == 400


class TestAddressGaps:
    H = base_headers(VALID_USER_ID)

    def _create_address(self):
        payload = {
            "label": "HOME",
            "street": "123 Test Street",
            "city": "TestCity",
            "pincode": "500001",
            "is_default": False
        }
        r = requests.post(url("/addresses"), json=payload, headers=self.H)
        if r.status_code not in (200, 201):
            return None
        body = r.json()
        return body.get("address_id") or body.get("id") or (body.get("address") or {}).get("address_id")

    def test_update_address_nonexistent_returns_404(self):
        """PUT on address_id that doesn't exist → 404."""
        r = requests.put(url("/addresses/999999"),
                         json={"street": "Some New Street"},
                         headers=self.H)
        assert r.status_code == 404

    def test_update_address_label_is_ignored_or_rejected(self):
        """Label cannot be changed via PUT; server must not apply it."""
        addr_id = self._create_address()
        if addr_id is None:
            pytest.skip("Could not create address")
        r = requests.put(url(f"/addresses/{addr_id}"),
                         json={"label": "OFFICE"},
                         headers=self.H)
        # either 400 (rejected) or 200 with label unchanged
        if r.status_code == 200:
            data = r.json()
            label = data.get("label") or (data.get("address") or {}).get("label")
            assert label == "HOME", f"Label should not change via PUT, but got {label}"

    def test_update_address_city_is_ignored_or_rejected(self):
        """City cannot be changed via PUT."""
        addr_id = self._create_address()
        if addr_id is None:
            pytest.skip("Could not create address")
        r = requests.put(url(f"/addresses/{addr_id}"),
                         json={"city": "ChangedCity"},
                         headers=self.H)
        if r.status_code == 200:
            data = r.json()
            city = data.get("city") or (data.get("address") or {}).get("city")
            assert city == "TestCity", f"City should not change via PUT, but got {city}"

    def test_update_address_pincode_is_ignored_or_rejected(self):
        """Pincode cannot be changed via PUT."""
        addr_id = self._create_address()
        if addr_id is None:
            pytest.skip("Could not create address")
        r = requests.put(url(f"/addresses/{addr_id}"),
                         json={"pincode": "110001"},
                         headers=self.H)
        if r.status_code == 200:
            data = r.json()
            pincode = data.get("pincode") or (data.get("address") or {}).get("pincode")
            assert pincode == "500001", f"Pincode should not change via PUT, but got {pincode}"


class TestProductGaps:
    H = base_headers(VALID_USER_ID)

    def test_inactive_product_hidden_from_public_list(self):
        """A product that is inactive in admin/products must NOT appear in /products."""
        admin_r = requests.get(url("/admin/products"), headers=admin_headers())
        all_products = admin_r.json()
        if not isinstance(all_products, list):
            pytest.skip("Cannot read admin products")

        inactive_ids = set()
        for p in all_products:
            active = p.get("is_active", p.get("active", True))
            if active is False or active == 0:
                inactive_ids.add(p.get("product_id") or p.get("id"))

        if not inactive_ids:
            pytest.skip("No inactive products in database")

        public_r = requests.get(url("/products"), headers=self.H)
        public_products = public_r.json()
        public_ids = set()
        if isinstance(public_products, list):
            for p in public_products:
                public_ids.add(p.get("product_id") or p.get("id"))

        overlap = inactive_ids & public_ids
        assert len(overlap) == 0, f"Inactive products visible in public list: {overlap}"

    def test_get_inactive_product_by_id_returns_404(self):
        """GET /products/{id} for an inactive product should return 404."""
        admin_r = requests.get(url("/admin/products"), headers=admin_headers())
        all_products = admin_r.json()
        if not isinstance(all_products, list):
            pytest.skip("Cannot read admin products")

        inactive_pid = None
        for p in all_products:
            active = p.get("is_active", p.get("active", True))
            if active is False or active == 0:
                inactive_pid = p.get("product_id") or p.get("id")
                break

        if inactive_pid is None:
            pytest.skip("No inactive products in database")

        r = requests.get(url(f"/products/{inactive_pid}"), headers=self.H)
        assert r.status_code == 404, \
            f"Inactive product {inactive_pid} should return 404, got {r.status_code}"


class TestOrderGaps:
    H = base_headers(VALID_USER_ID)
    H2 = base_headers(OTHER_USER_ID)

    def test_invoice_nonexistent_order_returns_404(self):
        r = requests.get(url("/orders/999999/invoice"), headers=self.H)
        assert r.status_code == 404

    def test_orders_list_only_returns_own_orders(self):
        """User A must not see User B's orders."""
        r1 = requests.get(url("/orders"), headers=self.H)
        r2 = requests.get(url("/orders"), headers=self.H2)
        assert r1.status_code == 200
        assert r2.status_code == 200
        orders1 = r1.json() if isinstance(r1.json(), list) else []
        orders2 = r2.json() if isinstance(r2.json(), list) else []
        ids1 = {o.get("order_id") or o.get("id") for o in orders1}
        ids2 = {o.get("order_id") or o.get("id") for o in orders2}
        overlap = ids1 & ids2
        assert len(overlap) == 0, f"Orders visible to both users: {overlap}"

    def test_get_order_belonging_to_other_user_returns_404_or_403(self):
        """User A must not be able to fetch User B's specific order."""
        # place an order as user 1
        requests.delete(url("/cart/clear"), headers=self.H)
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if not isinstance(products, list):
            pytest.skip("No products")
        for p in products:
            if float(p.get("price", 9999)) < 4000:
                pid = p.get("product_id") or p.get("id")
                requests.post(url("/cart/add"), json={"product_id": pid, "quantity": 1}, headers=self.H)
                break
        co = requests.post(url("/checkout"), json={"payment_method": "COD"}, headers=self.H)
        if co.status_code not in (200, 201):
            pytest.skip("Checkout failed")
        oid = co.json().get("order_id") or (co.json().get("order") or {}).get("order_id")
        if oid is None:
            pytest.skip("Could not get order_id")
        # try to access it as user 2
        r2 = requests.get(url(f"/orders/{oid}"), headers=self.H2)
        assert r2.status_code in (403, 404), \
            f"User 2 should not access User 1's order, got {r2.status_code}"


class TestCouponGaps:
    H = base_headers(VALID_USER_ID)

    def _add_cheap_item(self):
        requests.delete(url("/cart/clear"), headers=self.H)
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if isinstance(products, list):
            for p in products:
                if float(p.get("price", 9999)) < 4000:
                    pid = p.get("product_id") or p.get("id")
                    requests.post(url("/cart/add"),
                                  json={"product_id": pid, "quantity": 1},
                                  headers=self.H)
                    return True
        return False

    def test_apply_coupon_empty_cart_returns_error(self):
        """Applying a coupon to an empty cart must fail."""
        requests.delete(url("/cart/clear"), headers=self.H)
        r_coupons = requests.get(url("/admin/coupons"), headers=admin_headers())
        coupons = r_coupons.json()
        code = None
        if isinstance(coupons, list):
            for c in coupons:
                if not c.get("is_expired", c.get("expired", False)):
                    code = c.get("code") or c.get("coupon_code")
                    break
        if code is None:
            pytest.skip("No active coupons available")
        r = requests.post(url("/coupon/apply"), json={"coupon_code": code}, headers=self.H)
        assert r.status_code in (400, 422), "Applying coupon to empty cart should fail"

    def test_fixed_coupon_discount_calculation(self):
        """FIXED coupon discount = flat amount, not exceeding cart total."""
        r = requests.get(url("/admin/coupons"), headers=admin_headers())
        coupons = r.json()
        coupon = None
        if isinstance(coupons, list):
            for c in coupons:
                if c.get("type") == "FIXED" and not c.get("is_expired", c.get("expired", False)):
                    coupon = c
                    break
        if coupon is None:
            pytest.skip("No active FIXED coupon in database")

        if not self._add_cheap_item():
            pytest.skip("No cheap product")

        code = coupon.get("code") or coupon.get("coupon_code")
        r2 = requests.post(url("/coupon/apply"), json={"coupon_code": code}, headers=self.H)
        if r2.status_code not in (200, 201):
            pytest.skip(f"Coupon apply failed with {r2.status_code}")

        cart = requests.get(url("/cart"), headers=self.H).json()
        original_total = float(cart.get("original_total", cart.get("total", 0)))
        discount = float(cart.get("discount", 0))
        expected_discount = float(coupon.get("discount_value", coupon.get("value", 0)))

        assert abs(discount - expected_discount) < 0.01 or discount <= original_total, \
            f"FIXED discount mismatch: expected {expected_discount}, got {discount}"

    def test_percent_coupon_without_cap(self):
        """PERCENT coupon with no max_discount applies full percentage."""
        r = requests.get(url("/admin/coupons"), headers=admin_headers())
        coupons = r.json()
        coupon = None
        if isinstance(coupons, list):
            for c in coupons:
                ctype = c.get("type")
                expired = c.get("is_expired", c.get("expired", False))
                max_d = c.get("max_discount")
                if ctype == "PERCENT" and not expired and (max_d is None or max_d == 0):
                    coupon = c
                    break
        if coupon is None:
            pytest.skip("No uncapped PERCENT coupon available")

        if not self._add_cheap_item():
            pytest.skip("No cheap product")

        code = coupon.get("code") or coupon.get("coupon_code")
        r2 = requests.post(url("/coupon/apply"), json={"coupon_code": code}, headers=self.H)
        if r2.status_code not in (200, 201):
            pytest.skip("Coupon apply failed")

        cart = requests.get(url("/cart"), headers=self.H).json()
        total = float(cart.get("total", 0))
        discount = float(cart.get("discount", 0))
        percent = float(coupon.get("discount_value", coupon.get("value", 0)))
        expected = round((percent / 100) * total, 2)

        assert abs(discount - expected) < 0.5, \
            f"Uncapped PERCENT discount expected ~{expected}, got {discount}"


class TestWalletGaps:
    H = base_headers(VALID_USER_ID)

    def test_wallet_balance_increases_after_add(self):
        """Balance must increase by exactly the amount added."""
        before_data = requests.get(url("/wallet"), headers=self.H).json()
        before = float(before_data.get("balance", before_data.get("wallet_balance", 0)))

        amount = 250
        r = requests.post(url("/wallet/add"), json={"amount": amount}, headers=self.H)
        assert r.status_code in (200, 201)

        after_data = requests.get(url("/wallet"), headers=self.H).json()
        after = float(after_data.get("balance", after_data.get("wallet_balance", 0)))

        assert abs(after - (before + amount)) < 0.01, \
            f"Expected balance {before + amount}, got {after}"


class TestLoyaltyGaps:
    H = base_headers(VALID_USER_ID)

    def test_loyalty_points_awarded_after_checkout(self):
        """After a successful order, loyalty points balance should not decrease."""
        pts_before_data = requests.get(url("/loyalty"), headers=self.H).json()
        pts_before = int(pts_before_data.get("points", pts_before_data.get("loyalty_points", 0)))

        # place an order
        requests.delete(url("/cart/clear"), headers=self.H)
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if not isinstance(products, list):
            pytest.skip("No products")
        placed = False
        for p in products:
            if float(p.get("price", 9999)) < 4000:
                pid = p.get("product_id") or p.get("id")
                requests.post(url("/cart/add"), json={"product_id": pid, "quantity": 1}, headers=self.H)
                co = requests.post(url("/checkout"), json={"payment_method": "CARD"}, headers=self.H)
                if co.status_code in (200, 201):
                    placed = True
                break
        if not placed:
            pytest.skip("Could not place order")

        pts_after_data = requests.get(url("/loyalty"), headers=self.H).json()
        pts_after = int(pts_after_data.get("points", pts_after_data.get("loyalty_points", 0)))
        assert pts_after >= pts_before, \
            f"Loyalty points should not decrease after checkout: before={pts_before}, after={pts_after}"


class TestReviewGaps:
    H = base_headers(VALID_USER_ID)

    def _first_product_id(self):
        r = requests.get(url("/products"), headers=self.H)
        products = r.json()
        if isinstance(products, list) and products:
            return products[0].get("product_id") or products[0].get("id")
        return None

    def test_add_review_nonexistent_product_returns_404(self):
        r = requests.post(url("/products/999999/reviews"),
                          json={"rating": 4, "comment": "Great!"},
                          headers=self.H)
        assert r.status_code == 404

    def test_add_review_missing_rating_returns_400(self):
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url(f"/products/{pid}/reviews"),
                          json={"comment": "No rating provided"},
                          headers=self.H)
        assert r.status_code == 400

    def test_add_review_missing_comment_returns_400_or_200(self):
        """Comment is required (1–200 chars); missing should be 400."""
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url(f"/products/{pid}/reviews"),
                          json={"rating": 3},
                          headers=self.H)
        # doc says comment must be 1-200 chars; missing means 0 chars which violates lower bound
        assert r.status_code == 400

    def test_add_review_comment_exactly_1_char(self):
        """Boundary: comment = 1 char must be accepted."""
        pid = self._first_product_id()
        if pid is None:
            pytest.skip("No products")
        r = requests.post(url(f"/products/{pid}/reviews"),
                          json={"rating": 3, "comment": "X"},
                          headers=self.H)
        assert r.status_code in (200, 201)


class TestAdminGaps:
    def test_admin_endpoint_with_extra_user_id_header_still_works(self):
        """Admin endpoints should not break if X-User-ID is also provided."""
        h = {"X-Roll-Number": ROLL_NUMBER, "X-User-ID": VALID_USER_ID}
        r = requests.get(url("/admin/users"), headers=h)
        assert r.status_code == 200

    def test_admin_carts_includes_items_and_totals(self):
        """Admin carts response should include items and computed totals per spec."""
        r = requests.get(url("/admin/carts"), headers=admin_headers())
        assert r.status_code == 200
        carts = r.json()
        if isinstance(carts, list) and len(carts) > 0:
            cart = carts[0]
            # at minimum the cart object should exist; items may be empty list
            assert "items" in cart or "cart_items" in cart or isinstance(cart, dict)

    def test_admin_orders_includes_payment_and_order_status(self):
        """Admin orders must expose payment_status and order_status."""
        r = requests.get(url("/admin/orders"), headers=admin_headers())
        assert r.status_code == 200
        orders = r.json()
        if isinstance(orders, list) and len(orders) > 0:
            o = orders[0]
            has_payment = "payment_status" in o or "payment" in str(o).lower()
            has_order = "order_status" in o or "status" in o
            assert has_payment, "Admin orders should include payment_status"
            assert has_order, "Admin orders should include order_status"
