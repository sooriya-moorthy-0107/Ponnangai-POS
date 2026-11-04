import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["PRODUCTION"] = "False"

from main import app
from app.models.database import SessionLocal
from app.models.domain import User, Product, ShopInventory, Bill, BillItem
from app.core.security import pwd_context, login_rate_limiter
import app.api.dependencies as deps

client = TestClient(app)


def test_security_headers_present():
    """Verify essential defense-in-depth security headers are set on HTTP responses."""
    response = client.get("/login")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "SAMEORIGIN"
    assert response.headers.get("x-xss-protection") == "1; mode=block"
    assert "Content-Security-Policy" in response.headers


def test_login_rate_limiting():
    """Verify that exceeding the login rate limit returns HTTP 429 Too Many Requests."""
    test_ip = "192.0.2.99"
    # Reset limiter for test IP
    login_rate_limiter._records[test_ip].clear()

    # Make 5 attempts (allowed)
    for _ in range(5):
        resp = client.post(
            "/login",
            data={"username": "invalid_user", "password": "wrong_password"},
            headers={"x-forwarded-for": test_ip}
        )
        assert resp.status_code in [200, 401]

    # 6th attempt must be blocked by rate limiter
    resp_blocked = client.post(
        "/login",
        data={"username": "invalid_user", "password": "wrong_password"},
        headers={"x-forwarded-for": test_ip}
    )
    assert resp_blocked.status_code == 429
    assert "Too many login" in resp_blocked.text
    assert "Retry-After" in resp_blocked.headers


def test_unauthenticated_admin_endpoints_blocked():
    """Verify that unprotected maintenance endpoints now strictly require authorization."""
    # Debug photos should reject unauthenticated requests
    resp = client.get("/api/debug/photos")
    assert resp.status_code in [401, 403]

    # Fix photos should reject unauthenticated requests
    resp = client.get("/api/system/fix_photos")
    assert resp.status_code in [401, 403]

    # Map photos should reject unauthenticated requests
    resp = client.get("/api/system/map_photos")
    assert resp.status_code in [401, 403]


def test_bill_idor_prevention():
    """Verify that a shopkeeper cannot view or revert another shopkeeper's bill."""
    db = SessionLocal()
    try:
        # Create two test shopkeepers
        sk1 = db.query(User).filter(User.username == "test_sk_1").first()
        if not sk1:
            sk1 = User(username="test_sk_1", password=pwd_context.hash("pass"), role="Shopkeeper")
            db.add(sk1)
            db.commit()
            db.refresh(sk1)

        sk2 = db.query(User).filter(User.username == "test_sk_2").first()
        if not sk2:
            sk2 = User(username="test_sk_2", password=pwd_context.hash("pass"), role="Shopkeeper")
            db.add(sk2)
            db.commit()
            db.refresh(sk2)

        # Create a bill owned by sk1
        bill = Bill(
            cashier_id=sk1.id,
            cashier_name=sk1.username,
            total_amount=100.0,
            final_amount=100.0,
            payment_mode="Cash"
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)

        import app.api.routes.billing as billing_module
        orig_dep = billing_module.get_current_user
        billing_module.get_current_user = lambda request, db=None: sk2

        try:
            # sk2 attempts to view sk1's bill -> must be 403
            resp = client.get(f"/api/bills/{bill.id}")
            assert resp.status_code == 403

            # sk2 attempts to revert sk1's bill -> must be 403
            resp = client.post(f"/api/bills/{bill.id}/revert")
            assert resp.status_code == 403
        finally:
            billing_module.get_current_user = orig_dep

    finally:
        db.close()


def test_retail_shopkeeper_price_tampering_blocked():
    """Verify that retail shopkeepers cannot tamper with product prices in create_bill."""
    db = SessionLocal()
    try:
        sk = db.query(User).filter(User.username == "test_sk_price").first()
        if not sk:
            sk = User(username="test_sk_price", password=pwd_context.hash("pass"), role="Shopkeeper")
            db.add(sk)
            db.commit()
            db.refresh(sk)

        prod = db.query(Product).filter(Product.name == "Secure Price Test Item").first()
        if not prod:
            prod = Product(
                name="Secure Price Test Item",
                price=250.0,
                shopkeeper_id=sk.id,
                product_type="solid",
                unit="Pcs"
            )
            db.add(prod)
            db.commit()
            db.refresh(prod)

        inv = db.query(ShopInventory).filter(ShopInventory.product_id == prod.id, ShopInventory.shopkeeper_id == sk.id).first()
        if not inv:
            inv = ShopInventory(product_id=prod.id, shopkeeper_id=sk.id, stock=50)
            db.add(inv)
            db.commit()

        import app.api.routes.billing as billing_module
        orig_dep = billing_module.get_current_user
        billing_module.get_current_user = lambda request, db=None: sk

        try:
            # Tampered request payload: client attempts to bill a Rs 250 item at Rs 1.00
            payload = {
                "items": [{"id": prod.id, "qty": 1, "price": 1.0}],
                "payment_mode": "Cash"
            }
            resp = client.post("/api/bills", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            # Server must enforce product.price (250.0), NOT client's 1.0!
            assert data["bill"]["total_amount"] == 250.0
            assert data["bill"]["final_amount"] == 250.0
            assert data["bill"]["items"][0]["price"] == 250.0
        finally:
            billing_module.get_current_user = orig_dep

    finally:
        db.close()
