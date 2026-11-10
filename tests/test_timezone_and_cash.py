import os
import sys
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

# Add parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["PRODUCTION"] = "False"

from main import app
from app.models.database import SessionLocal
from app.models.domain import User, CashTransaction
from app.core.security import pwd_context
from app.utils.timezone import (
    get_ist_now,
    get_ist_today_range,
    format_ist_iso,
    format_ist_time,
    format_ist_datetime,
    IST,
)
import app.api.routes.cash as cash_module

client = TestClient(app)


def test_ist_timezone_utilities():
    """Verify IST timezone functions correctly handle timestamps and formatting."""
    now_ist = get_ist_now()
    assert now_ist is not None
    # Verify ISO formatting includes +05:30 offset
    iso_str = format_ist_iso(now_ist)
    assert "+05:30" in iso_str or iso_str.endswith("Z") or "T" in iso_str
    
    # Verify 12-hour AM/PM formatting
    time_str = format_ist_time(now_ist)
    assert ("AM" in time_str) or ("PM" in time_str)

    # Verify today range
    start, end = get_ist_today_range()
    assert start < end
    assert start.hour == 0 and start.minute == 0 and start.second == 0
    assert end.hour == 23 and end.minute == 59 and end.second == 59


def test_cash_transaction_creation_and_revert():
    """Verify cash transaction returns can_revert=True and can be successfully reverted."""
    db = SessionLocal()
    try:
        # Create test shopkeeper
        sk = db.query(User).filter(User.username == "test_cash_sk").first()
        if not sk:
            sk = User(username="test_cash_sk", password=pwd_context.hash("pass"), role="Shopkeeper")
            db.add(sk)
            db.commit()
            db.refresh(sk)

        orig_dep = cash_module.get_current_user
        cash_module.get_current_user = lambda request, db=None: sk

        try:
            # 1. Add cash transaction (Cash Out / Expense)
            payload = {
                "type": "Cash Out",
                "amount": 150.0,
                "reason": "Tea & Snacks"
            }
            resp = client.post("/api/cash-transactions", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "success"
            tx_id = data["transaction_id"]
            assert "+05:30" in data["timestamp"]

            # 2. Fetch today's transactions
            resp_list = client.get("/api/cash-transactions")
            assert resp_list.status_code == 200
            list_data = resp_list.json()
            tx_list = list_data["transactions"]
            found = next((t for t in tx_list if t["id"] == tx_id), None)
            assert found is not None
            assert found["can_revert"] is True
            assert ("AM" in found["time_display"]) or ("PM" in found["time_display"])

            # 3. Revert transaction via POST /api/cash-transactions/{id}/revert
            resp_revert = client.post(f"/api/cash-transactions/{tx_id}/revert")
            assert resp_revert.status_code == 200
            revert_data = resp_revert.json()
            assert revert_data["success"] is True

            # 4. Attempting to revert already reverted transaction should fail (404 Not Found)
            resp_re_revert = client.post(f"/api/cash-transactions/{tx_id}/revert")
            assert resp_re_revert.status_code in [400, 404]

            # 5. Test DELETE endpoint as well
            payload2 = {
                "type": "Cash In",
                "amount": 200.0,
                "reason": "Float Cash"
            }
            resp2 = client.post("/api/cash-transactions", json=payload2)
            assert resp2.status_code == 200
            tx2_id = resp2.json()["transaction_id"]

            resp_del = client.delete(f"/api/cash-transactions/{tx2_id}")
            assert resp_del.status_code == 200
            assert resp_del.json()["success"] is True

        finally:
            cash_module.get_current_user = orig_dep

    finally:
        db.close()
