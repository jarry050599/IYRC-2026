import os
from pathlib import Path

DB_FILE = Path(__file__).parent / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{DB_FILE}"
os.environ["ADMIN_PASSWORD"] = "test-password"

from fastapi.testclient import TestClient
from app.main import app


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
            "name": "測試會員", "phone": "0912", "role": "member",
            "card_uid": "AA:BB:CC", "status": "active"
        })
        assert created.status_code == 200
        tap = client.post("/api/nfc/tap", json={"card_uid": "AABBCC"})
        assert tap.json()["action"] == "check_in"
        rent = client.post("/api/rentals", json={"computer_id": "PC-01", "card_uid": "AABBCC"})
        assert rent.status_code == 200
        blocked = client.post("/api/nfc/tap", json={"card_uid": "AABBCC"})
        assert blocked.json()["action"] == "return_required"
        returned = client.patch("/api/rentals/return", json={"card_uid": "AABBCC"})
        assert returned.status_code == 200
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
            "name": "材料測試者", "role": "member", "card_uid": "MATCARD01", "status": "active"
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
