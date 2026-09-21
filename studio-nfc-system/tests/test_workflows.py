import os
from pathlib import Path

DB_FILE = Path(__file__).parent / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{DB_FILE}"
os.environ["ADMIN_PASSWORD"] = "test-password"

from datetime import timedelta

from fastapi.testclient import TestClient
from app.main import app
from app.models import now_local
from app.security import token_digest


def auth(client):
    response = client.post("/api/admin/login", json={"username": "admin", "password": "test-password"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_complete_attendance_and_rental_workflow():
    if DB_FILE.exists():
        DB_FILE.unlink()
    with TestClient(app) as client:
        headers = auth(client)
        created = client.post("/api/admin/users", headers=headers, json={
            "name": "測試會員", "class_name": "資一甲", "student_id": "TEST001",
            "grade": "一年級", "role": "member",
            "card_uid": "AA:BB:CC", "status": "active"
        })
        assert created.status_code == 200
        prepared_borrow = client.post("/api/rentals/prepare", json={"computer_id": "PC-01"})
        assert prepared_borrow.status_code == 200
        rent = client.post("/api/nfc/tap", json={"card_uid": "AABBCC"})
        assert rent.status_code == 200
        assert rent.json()["action"] == "rental_success"
        assert rent.json()["attendance"]["check_in_time"] is not None
        assert rent.json()["computers"][0]["status"] == "in_use"
        blocked = client.post("/api/nfc/tap", json={"card_uid": "AABBCC"})
        assert blocked.json()["action"] == "return_required"
        prepared = client.post("/api/rentals/return/prepare", json={"computer_id": "PC-01"})
        assert prepared.status_code == 200
        wrong_user = client.post("/api/admin/users", headers=headers, json={
            "name": "其他會員", "class_name": "資二甲", "student_id": "TEST002",
            "grade": "二年級", "role": "member", "card_uid": "WRONGCARD", "status": "active"
        })
        assert wrong_user.status_code == 200
        wrong_card = client.post("/api/nfc/tap", json={"card_uid": "WRONGCARD"})
        assert wrong_card.json()["action"] == "return_auth_error"
        returned = client.post("/api/nfc/tap", json={"card_uid": "AABBCC"})
        assert returned.status_code == 200
        assert returned.json()["action"] == "return_success"
        assert returned.json()["computers"][0]["status"] == "available"
        checkout = client.post("/api/nfc/tap", json={"card_uid": "AABBCC"})
        assert checkout.json()["action"] == "check_out"


def test_unknown_card_and_one_computer_limit():
    with TestClient(app) as client:
        unknown = client.post("/api/nfc/tap", json={"card_uid": "NOPE"})
        assert unknown.status_code == 200
        assert unknown.json()["action"] == "unknown"


def test_material_crud_and_search_dropdown_data():
    with TestClient(app) as client:
        headers = auth(client)
        created = client.post("/api/admin/materials", headers=headers, json={
            "category": "resistor", "name": "金屬膜電阻", "specification": "10kΩ 1/4W 1%",
            "quantity": 50, "location": "A 櫃 3 號盒", "status": "active"
        })
        assert created.status_code == 200
        material_id = created.json()["id"]
        found = client.get("/api/admin/materials?search=10k&category=resistor", headers=headers)
        assert len(found.json()) == 1
        updated = client.put(f"/api/admin/materials/{material_id}", headers=headers, json={
            "category": "resistor", "name": "金屬膜電阻", "specification": "10kΩ 1/4W 1%",
            "quantity": 48, "location": "A 櫃 3 號盒", "status": "active"
        })
        assert updated.json()["quantity"] == 48
        assert updated.json()["updated_at"] is not None
        detail = client.get(f"/api/admin/materials/{material_id}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["location"] == "A 櫃 3 號盒"
        disabled = client.delete(f"/api/admin/materials/{material_id}", headers=headers)
        assert disabled.json()["status"] == "disabled"


def test_admin_settings_offline_reports_audit_and_persistence():
    with TestClient(app) as client:
        headers = auth(client)
        offline = client.patch("/api/admin/computers/PC-04", headers=headers, json={"status": "offline"})
        assert offline.status_code == 200
        assert next(pc for pc in offline.json() if pc["id"] == "PC-04")["status"] == "offline"

        setting = client.put("/api/admin/settings", headers=headers, json={"closing_time": "23:58"})
        assert setting.status_code == 200
        assert client.get("/api/admin/settings", headers=headers).json()["closing_time"] == "23:58"

        report = client.get("/api/admin/reports/members?month=2026-09", headers=headers)
        assert report.status_code == 200
        csv_report = client.get("/api/admin/reports/members/csv?month=2026-09", headers=headers)
        assert csv_report.status_code == 200
        assert "text/csv" in csv_report.headers["content-type"]

        logs = client.get("/api/admin/audit-logs", headers=headers)
        assert logs.status_code == 200
        actions = {row["action"] for row in logs.json()}
        assert {"computer_status", "update_setting", "update_material"} <= actions

    # A new application lifespan/client must read the same values from SQLite.
    with TestClient(app) as restarted_client:
        restarted_headers = auth(restarted_client)
        computers = restarted_client.get("/api/admin/dashboard", headers=restarted_headers).json()["computers"]
        assert next(pc for pc in computers if pc["id"] == "PC-04")["status"] == "offline"
        assert restarted_client.get("/api/admin/settings", headers=restarted_headers).json()["closing_time"] == "23:58"
        restored = restarted_client.patch("/api/admin/computers/PC-04", headers=restarted_headers,
                                          json={"status": "available"})
        assert restored.status_code == 200


def test_admin_endpoints_require_authentication():
    with TestClient(app) as client:
        for path in ("/api/admin/dashboard", "/api/admin/users", "/api/admin/materials",
                     "/api/admin/attendance", "/api/admin/rentals", "/api/admin/settings",
                     "/api/admin/audit-logs"):
            assert client.get(path).status_code == 401


def test_material_checkout_idempotency_stock_return_audit_and_persistence():
    with TestClient(app) as client:
        headers = auth(client)
        user = client.post("/api/admin/users", headers=headers, json={
            "name": "材料測試者", "class_name": "資三甲", "student_id": "TEST003",
            "grade": "三年級", "role": "member", "card_uid": "MATCARD01", "status": "active"
        })
        assert user.status_code == 200
        consumable = client.post("/api/admin/materials", headers=headers, json={
            "category": "resistor", "name": "測試消耗材料", "specification": "10Ω",
            "material_type": "consumable", "quantity": 10, "location": "T-01", "status": "active"
        }).json()
        returnable = client.post("/api/admin/materials", headers=headers, json={
            "category": "transistor", "name": "測試可歸還材料", "specification": "TOOL",
            "material_type": "returnable", "quantity": 10, "location": "T-02", "status": "active"
        }).json()

        tap = client.post("/api/nfc/tap", json={"card_uid": "MATCARD01"})
        assert tap.json()["action"] == "check_in"
        material_headers = {"Authorization": f"Bearer {tap.json()['material_token']}"}

        first = client.post("/api/material-rentals", headers=material_headers, json={
            "material_id": consumable["id"], "quantity": 3, "request_id": "checkout-once"
        })
        assert first.status_code == 200
        assert first.json()["remaining_quantity"] == 7
        assert first.json()["rental"]["status"] == "consumed"

        duplicate = client.post("/api/material-rentals", headers=material_headers, json={
            "material_id": consumable["id"], "quantity": 3, "request_id": "checkout-once"
        })
        assert duplicate.status_code == 200
        assert duplicate.json()["remaining_quantity"] == 7

        insufficient = client.post("/api/material-rentals", headers=material_headers, json={
            "material_id": consumable["id"], "quantity": 8, "request_id": "too-many"
        })
        assert insufficient.status_code == 409
        assert "目前僅剩 7 個" in insufficient.json()["detail"]
        assert client.get(f"/api/admin/materials/{consumable['id']}", headers=headers).json()["quantity"] == 7

        borrowed = client.post("/api/material-rentals", headers=material_headers, json={
            "material_id": returnable["id"], "quantity": 3, "request_id": "returnable-once"
        })
        assert borrowed.status_code == 200
        assert borrowed.json()["remaining_quantity"] == 7
        rental_id = borrowed.json()["rental"]["id"]
        returned = client.post(f"/api/material-rentals/{rental_id}/return", headers=material_headers)
        assert returned.status_code == 200
        assert returned.json()["remaining_quantity"] == 10
        assert returned.json()["rental"]["status"] == "returned"
        assert returned.json()["rental"]["returned_at"] is not None
        assert client.post(f"/api/material-rentals/{rental_id}/return", headers=material_headers).status_code == 409

        mine = client.get("/api/material-rentals/mine", headers=material_headers)
        assert mine.status_code == 200
        assert len(mine.json()) == 2
        admin_records = client.get("/api/admin/material-rentals", headers=headers)
        assert admin_records.status_code == 200
        assert {row["status"] for row in admin_records.json()} >= {"consumed", "returned"}
        actions = {row["action"] for row in client.get("/api/admin/audit-logs", headers=headers).json()}
        assert {"material_borrow", "material_return"} <= actions

    with TestClient(app) as restarted_client:
        restarted_headers = auth(restarted_client)
        assert restarted_client.get(f"/api/admin/materials/{consumable['id']}",
                                    headers=restarted_headers).json()["quantity"] == 7
        assert restarted_client.get(f"/api/admin/materials/{returnable['id']}",
                                    headers=restarted_headers).json()["quantity"] == 10


def test_qr_inventory_auto_slotting_low_stock_and_audit():
    with TestClient(app) as client:
        headers = auth(client)
        created = client.post("/api/items", headers=headers, json={
            "name": "精密電阻", "category": "材料", "subcategory": "電阻",
            "manufacturer": "Maker Parts", "mpn": "R-10K-TEST",
            "specs": {"resistance": "10kΩ", "tolerance": "1%", "power": "1/4W"},
            "total_quantity": 8, "safe_stock_level": 5
        })
        assert created.status_code == 201
        item = created.json()
        assert len(item["slots"]) == 1

        found = client.get("/api/items?keyword=10kΩ&subcategory=電阻", headers=headers)
        assert any(row["id"] == item["id"] for row in found.json())
        added = client.post("/api/inventory/in", headers=headers,
                            json={"item_id": item["id"], "quantity": 2})
        assert added.status_code == 200
        assert added.json()["slot_code"] == item["slots"][0]["code"]
        assert added.json()["item"]["total_quantity"] == 10

        removed = client.post("/api/inventory/out", headers=headers,
                              json={"item_id": item["id"], "quantity": 6})
        assert removed.status_code == 200
        assert removed.json()["item"]["low_stock"] is True
        low = client.get("/api/slots/low-stock", headers=headers).json()
        assert any(row["id"] == item["id"] for row in low)
        slot = client.get(f"/api/slots/{item['slots'][0]['code']}", headers=headers).json()
        assert any(row["item_id"] == item["id"] for row in slot["items"])
        labels = client.get("/api/slots/labels.pdf", headers=headers)
        assert labels.status_code == 200
        assert labels.content.startswith(b"%PDF")

        actions = {row["action"] for row in client.get("/api/admin/audit-logs", headers=headers).json()}
        assert {"item_create", "inventory_in", "inventory_out"} <= actions


def test_tool_qr_borrow_return_and_records():
    with TestClient(app) as client:
        headers = auth(client)
        borrower = client.post("/api/admin/users", headers=headers, json={
            "name": "工具借用者", "class_name": "資一乙", "student_id": "TEST004",
            "grade": "一年級", "role": "member", "card_uid": "TOOLCARD01", "status": "active"
        }).json()
        slot_id = client.get("/api/slots?keyword=B150", headers=headers).json()[0]["id"]
        created = client.post("/api/items", headers=headers, json={
            "name": "數位電表", "category": "工具", "subcategory": "其他",
            "mpn": "TOOL-DMM-TEST", "specs": {}, "total_quantity": 1,
            "safe_stock_level": 0, "status": "在庫", "slot_id": slot_id
        })
        assert created.status_code == 201
        tool = created.json()
        resolved = client.get("/api/qr/resolve/TOOL-DMM-TEST", headers=headers).json()
        assert resolved == {"type": "tool", "id": tool["id"], "name": "數位電表", "status": "在庫"}

        borrowed = client.post(f"/api/tools/{tool['id']}/borrow", headers=headers,
                               json={"user_id": borrower["id"]})
        assert borrowed.status_code == 200
        assert borrowed.json()["item"]["current_borrower_name"] == "工具借用者"
        assert client.post(f"/api/tools/{tool['id']}/borrow", headers=headers,
                           json={"user_id": borrower["id"]}).status_code == 409
        returned = client.post(f"/api/tools/{tool['id']}/return", headers=headers)
        assert returned.status_code == 200
        assert returned.json()["item"]["status"] == "在庫"
        records = client.get("/api/tool-rentals", headers=headers).json()
        assert any(row["item_id"] == tool["id"] and row["status"] == "returned" for row in records)
        actions = {row["action"] for row in client.get("/api/admin/audit-logs", headers=headers).json()}
        assert {"tool_borrow", "tool_return"} <= actions


def test_admin_session_is_database_backed_expires_and_logs_out():
    with TestClient(app) as client:
        headers = auth(client)
        assert client.get("/api/admin/users", headers=headers).status_code == 200

    # A new lifespan must resolve the token, and only from SQLite (checked below).
    with TestClient(app) as restarted:
        assert restarted.get("/api/admin/users", headers=headers).status_code == 200

        forged = {"Authorization": "Bearer not-a-real-token"}
        assert restarted.get("/api/admin/users", headers=forged).status_code == 401

        # The raw token is never stored, only its digest.
        raw = headers["Authorization"].removeprefix("Bearer ")
        from app.database import SessionLocal
        from app.models import AdminSession
        with SessionLocal() as db:
            assert db.get(AdminSession, raw) is None
            session = db.get(AdminSession, token_digest(raw))
            assert session is not None and session.expires_at > now_local()
            # Expire it in place; the next call must reject and clean it up.
            session.expires_at = now_local() - timedelta(seconds=1)
            db.commit()
        assert restarted.get("/api/admin/users", headers=headers).status_code == 401
        with SessionLocal() as db:
            assert db.get(AdminSession, token_digest(raw)) is None

    # Logging out deletes the row, so no later process can accept the token.
    with TestClient(app) as client:
        fresh = auth(client)
        assert client.post("/api/admin/logout", headers=fresh).status_code == 200
    with TestClient(app) as restarted:
        assert restarted.get("/api/admin/users", headers=fresh).status_code == 401
