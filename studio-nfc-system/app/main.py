from __future__ import annotations

import asyncio
import csv
import io
import json
import os
import secrets
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, inspect, or_, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from .database import Base, SessionLocal, engine, get_db
from .models import (AttendanceRecord, AuditLog, Computer, Inventory, Item, Material,
                     MaterialRental, RentalRecord, Setting, Slot, ToolRental, User, now_local)
from .security import TOKENS, default_admin_password, hash_password, new_token, verify_password

STATIC = Path(__file__).resolve().parent / "static"
connections: set[WebSocket] = set()
binding: dict[str, Any] = {"user_id": None, "admin_id": None, "expires": None}
material_mode: dict[str, Any] = {"expires": None}
material_sessions: dict[str, tuple[int, datetime]] = {}
last_auto_close: Optional[date] = None


class TapIn(BaseModel):
    card_uid: str = Field(min_length=2, max_length=80)


class RentalIn(TapIn):
    computer_id: str


class LoginIn(BaseModel):
    username: str
    password: str


class UserIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    phone: Optional[str] = None
    role: str
    card_uid: Optional[str] = None
    status: str = "active"
    password: Optional[str] = None


class AttendanceEdit(BaseModel):
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    note: str = "管理員修正"


class RentalEdit(BaseModel):
    borrowed_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    note: str = "管理員修正"


class ComputerPatch(BaseModel):
    status: str


class SettingPatch(BaseModel):
    closing_time: str


class MaterialIn(BaseModel):
    category: str
    name: str = Field(min_length=1, max_length=100)
    specification: Optional[str] = None
    quantity: int = Field(default=0, ge=0)
    location: Optional[str] = None
    material_type: str = "consumable"
    status: str = "active"


class MaterialTakeIn(BaseModel):
    material_id: int
    quantity: int = Field(gt=0)
    request_id: Optional[str] = Field(default=None, max_length=80)


class ItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str
    subcategory: Optional[str] = None
    manufacturer: Optional[str] = None
    mpn: Optional[str] = None
    specs: dict[str, Any] = Field(default_factory=dict)
    total_quantity: int = Field(default=0, ge=0)
    safe_stock_level: int = Field(default=0, ge=0)
    status: Optional[str] = None
    slot_id: Optional[int] = None


class InventoryIn(BaseModel):
    item_id: int
    quantity: int = Field(gt=0)
    slot_id: Optional[int] = None
    batch_no: Optional[str] = None
    received_date: Optional[date] = None


class InventoryOut(BaseModel):
    item_id: int
    quantity: int = Field(gt=0)


class SlotIn(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    cabinet: str = Field(min_length=1, max_length=20)
    parent_slot_id: Optional[int] = None
    capacity_hint: int = Field(default=1, ge=1)


class ToolBorrowIn(BaseModel):
    user_id: int
    expected_return_at: Optional[datetime] = None


def clean_uid(uid: str) -> str:
    return uid.strip().upper().replace(":", "").replace("-", "")


def dt(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat(timespec="seconds") if value else None


def user_json(user: User) -> dict:
    return {"id": user.id, "name": user.name, "phone": user.phone, "role": user.role,
            "card_uid": user.card_uid, "status": user.status, "created_at": dt(user.created_at)}


def attendance_json(row: AttendanceRecord) -> dict:
    return {"id": row.id, "user_id": row.user_id, "user_name": row.user.name,
            "check_in_time": dt(row.check_in_time), "check_out_time": dt(row.check_out_time),
            "type": row.type, "flag": row.flag}


def rental_json(row: RentalRecord) -> dict:
    seconds = int(((row.returned_at or now_local()) - row.borrowed_at).total_seconds())
    return {"id": row.id, "computer_id": row.computer_id, "user_id": row.user_id,
            "user_name": row.user.name, "borrowed_at": dt(row.borrowed_at),
            "returned_at": dt(row.returned_at), "duration_minutes": max(0, seconds // 60), "flag": row.flag}


def material_json(row: Material) -> dict:
    stock_status = "out" if row.quantity == 0 else "low" if row.quantity <= 10 else "normal"
    return {"id": row.id, "category": row.category, "name": row.name,
            "specification": row.specification, "quantity": row.quantity,
            "location": row.location, "material_type": row.material_type,
            "stock_status": stock_status, "status": row.status, "created_at": dt(row.created_at),
            "updated_at": dt(row.updated_at or row.created_at)}


def material_rental_json(row: MaterialRental) -> dict:
    return {"id": row.id, "user_id": row.user_id, "user_name": row.user.name,
            "material_id": row.material_id, "material_name": row.material.name,
            "specification": row.material.specification, "material_type": row.material.material_type,
            "quantity": row.quantity, "borrowed_at": dt(row.borrowed_at),
            "returned_at": dt(row.returned_at), "status": row.status,
            "created_at": dt(row.created_at), "updated_at": dt(row.updated_at)}


def item_json(row: Item, db: Session) -> dict:
    slots = db.execute(select(Slot.code, Inventory.quantity).join(Inventory).where(
        Inventory.item_id == row.id, Inventory.quantity > 0).order_by(Slot.code)).all()
    low_stock = row.category != "工具" and row.total_quantity <= row.safe_stock_level
    return {"id": row.id, "name": row.name, "category": row.category,
            "subcategory": row.subcategory, "manufacturer": row.manufacturer, "mpn": row.mpn,
            "specs": row.specs or {}, "total_quantity": row.total_quantity,
            "safe_stock_level": row.safe_stock_level, "low_stock": low_stock,
            "status": row.status, "current_borrower": row.current_borrower,
            "current_borrower_name": row.borrower.name if row.borrower else None,
            "borrowed_at": dt(row.borrowed_at), "expected_return_at": dt(row.expected_return_at),
            "slots": [{"code": code, "quantity": quantity} for code, quantity in slots],
            "created_at": dt(row.created_at), "updated_at": dt(row.updated_at)}


def tool_rental_json(row: ToolRental) -> dict:
    return {"id": row.id, "item_id": row.item_id, "tool_name": row.item.name,
            "user_id": row.user_id, "user_name": row.user.name,
            "borrowed_at": dt(row.borrowed_at), "expected_return_at": dt(row.expected_return_at),
            "returned_at": dt(row.returned_at), "status": row.status}


def issue_material_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    material_sessions[token] = (user_id, now_local() + timedelta(minutes=10))
    return token


def current_material_user(authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)) -> User:
    token = authorization.removeprefix("Bearer ") if authorization else ""
    session = material_sessions.get(token)
    if not session or session[1] <= now_local():
        material_sessions.pop(token, None)
        raise HTTPException(401, "請先感應 NFC 卡片驗證身份")
    user = db.get(User, session[0])
    if not user or user.status != "active" or user.role == "admin":
        raise HTTPException(403, "此使用者目前無法領用材料")
    if not active_attendance(db, user.id):
        raise HTTPException(403, "請先完成簽到再領用材料")
    return user


def revoke_material_sessions(user_id: int):
    for token, session in list(material_sessions.items()):
        if session[0] == user_id:
            material_sessions.pop(token, None)


def active_attendance(db: Session, user_id: int):
    return db.scalar(select(AttendanceRecord).where(
        AttendanceRecord.user_id == user_id, AttendanceRecord.check_out_time.is_(None)
    ).order_by(AttendanceRecord.check_in_time.desc()))


def active_rental(db: Session, user_id: int):
    return db.scalar(select(RentalRecord).options(joinedload(RentalRecord.computer)).where(
        RentalRecord.user_id == user_id, RentalRecord.returned_at.is_(None)
    ).order_by(RentalRecord.borrowed_at.desc()))


def computers_json(db: Session) -> list[dict]:
    result = []
    for pc in db.scalars(select(Computer).order_by(Computer.id)):
        item = {"id": pc.id, "name": pc.name, "status": pc.status, "user_name": None, "borrowed_at": None}
        if pc.status == "in_use":
            rental = db.scalar(select(RentalRecord).options(joinedload(RentalRecord.user)).where(
                RentalRecord.computer_id == pc.id, RentalRecord.returned_at.is_(None)))
            if rental:
                item.update(user_name=rental.user.name, borrowed_at=dt(rental.borrowed_at))
        result.append(item)
    return result


async def broadcast(event: dict):
    stale = []
    for ws in list(connections):
        try:
            await ws.send_json(event)
        except Exception:
            stale.append(ws)
    for ws in stale:
        connections.discard(ws)


def audit(db: Session, admin_id: int, action: str, target: str, detail: Any):
    db.add(AuditLog(admin_id=admin_id, action=action, target=target,
                    detail=json.dumps(detail, ensure_ascii=False, default=str)))


def current_admin(authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)) -> User:
    token = authorization.removeprefix("Bearer ") if authorization else ""
    user_id = TOKENS.get(token)
    user = db.get(User, user_id) if user_id else None
    if not user or user.role != "admin" or user.status != "active":
        raise HTTPException(401, "請先登入管理後台")
    return user


def init_db():
    Base.metadata.create_all(engine)
    # create_all does not alter an existing SQLite table; keep deployed databases compatible.
    material_columns = {column["name"] for column in inspect(engine).get_columns("materials")}
    if "updated_at" not in material_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE materials ADD COLUMN updated_at DATETIME"))
            connection.execute(text("UPDATE materials SET updated_at = created_at WHERE updated_at IS NULL"))
    material_columns = {column["name"] for column in inspect(engine).get_columns("materials")}
    if "material_type" not in material_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE materials ADD COLUMN material_type VARCHAR(20) NOT NULL DEFAULT 'consumable'"))
    with engine.begin() as connection:
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_open_attendance_user ON attendance_records(user_id) WHERE check_out_time IS NULL"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_open_rental_user ON rental_records(user_id) WHERE returned_at IS NULL"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_open_rental_computer ON rental_records(computer_id) WHERE returned_at IS NULL"))
    with SessionLocal() as db:
        for n in range(1, 5):
            pc_id = f"PC-{n:02d}"
            if not db.get(Computer, pc_id):
                db.add(Computer(id=pc_id, name=pc_id))
        if not db.scalar(select(Setting).where(Setting.key == "closing_time")):
            db.add(Setting(key="closing_time", value=os.getenv("CLOSING_TIME", "22:00")))
        if not db.scalar(select(User).where(User.role == "admin")):
            db.add(User(name="admin", role="admin", status="active",
                        password_hash=hash_password(default_admin_password())))
        db.commit()


async def auto_close_loop():
    global last_auto_close
    while True:
        try:
            now = now_local()
            with SessionLocal() as db:
                setting = db.get(Setting, "closing_time")
                close_at = time.fromisoformat(setting.value if setting else "22:00")
                if now.time() >= close_at and last_auto_close != now.date():
                    rentals = list(db.scalars(select(RentalRecord).where(RentalRecord.returned_at.is_(None))))
                    for rental in rentals:
                        rental.returned_at, rental.flag = now, "auto_returned"
                        rental.computer.status = "available"
                    records = list(db.scalars(select(AttendanceRecord).where(AttendanceRecord.check_out_time.is_(None))))
                    for record in records:
                        record.check_out_time, record.flag = now, "auto_closed"
                    db.commit()
                    last_auto_close = now.date()
                    await broadcast({"type": "auto_close", "message": "每日自動結算完成",
                                     "computers": computers_json(db)})
        except Exception as exc:
            print(f"auto close error: {exc}")
        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(auto_close_loop())
    yield
    task.cancel()


app = FastAPI(title="工作室 NFC 打卡與電腦租借系統", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def kiosk_page():
    return FileResponse(STATIC / "kiosk.html")


@app.get("/admin", include_in_schema=False)
def admin_page():
    return FileResponse(STATIC / "admin.html")


@app.get("/health")
def health():
    return {"status": "ok", "time": dt(now_local())}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        connections.discard(ws)


@app.get("/api/computers")
def get_computers(db: Session = Depends(get_db)):
    return computers_json(db)


@app.get("/api/materials")
def public_materials(search: Optional[str] = None, category: Optional[str] = None,
                     db: Session = Depends(get_db)):
    query = select(Material).where(Material.status == "active").order_by(Material.category, Material.name)
    if category:
        query = query.where(Material.category == category)
    if search:
        keyword = f"%{search.strip()}%"
        query = query.where(or_(Material.name.ilike(keyword), Material.specification.ilike(keyword),
                                Material.location.ilike(keyword)))
    return [material_json(row) for row in db.scalars(query)]


@app.post("/api/material-session/prepare")
def prepare_material_session():
    material_mode["expires"] = now_local() + timedelta(seconds=45)
    return {"ok": True, "message": "請在 45 秒內感應 NFC 卡片"}


@app.post("/api/nfc/tap")
async def nfc_tap(data: TapIn, db: Session = Depends(get_db)):
    uid = clean_uid(data.card_uid)
    if binding["user_id"] and binding["expires"] and binding["expires"] > now_local():
        conflict = db.scalar(select(User).where(User.card_uid == uid, User.id != binding["user_id"]))
        user = db.get(User, binding["user_id"])
        if conflict:
            result = {"ok": False, "action": "bind_error", "message": "此卡片已綁定其他使用者"}
        elif not user:
            result = {"ok": False, "action": "bind_error", "message": "找不到待綁定使用者"}
        else:
            user.card_uid = uid
            audit(db, binding["admin_id"], "bind_card", f"user:{user.id}", {"card_uid": uid})
            db.commit()
            result = {"ok": True, "action": "card_bound", "message": f"已綁定至 {user.name}", "user": user_json(user)}
        binding.update(user_id=None, admin_id=None, expires=None)
        await broadcast({"type": "nfc", **result})
        return result

    user = db.scalar(select(User).where(User.card_uid == uid, User.status == "active"))
    if not user or user.role == "admin":
        result = {"ok": False, "action": "unknown", "message": "卡片未註冊，請洽管理者綁卡"}
        await broadcast({"type": "nfc", **result})
        return result
    attendance = active_attendance(db, user.id)
    rental = active_rental(db, user.id)
    if material_mode["expires"] and material_mode["expires"] > now_local():
        if not attendance:
            attendance = AttendanceRecord(user_id=user.id,
                type="staff_shift" if user.role == "staff" else "member_visit")
            db.add(attendance)
            db.commit()
        material_mode["expires"] = None
        result = {"ok": True, "action": "material_auth", "message": "身份驗證成功",
                  "user": user_json(user), "material_token": issue_material_session(user.id),
                  "attendance": attendance_json(attendance), "computers": computers_json(db)}
        await broadcast({"type": "nfc", **result})
        return result
    if attendance and rental:
        result = {"ok": False, "action": "return_required", "message": f"請先歸還 {rental.computer_id}",
                  "user": user_json(user), "rental": rental_json(rental)}
    elif attendance:
        attendance.check_out_time = now_local()
        revoke_material_sessions(user.id)
        db.commit()
        result = {"ok": True, "action": "check_out", "message": "簽退成功", "user": user_json(user),
                  "attendance": attendance_json(attendance)}
    else:
        attendance = AttendanceRecord(user_id=user.id, type="staff_shift" if user.role == "staff" else "member_visit")
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        result = {"ok": True, "action": "check_in", "message": "簽到成功", "user": user_json(user),
                  "attendance": attendance_json(attendance), "material_token": issue_material_session(user.id)}
    result["computers"] = computers_json(db)
    await broadcast({"type": "nfc", **result})
    return result


@app.post("/api/material-rentals")
async def take_material(data: MaterialTakeIn, user: User = Depends(current_material_user),
                        db: Session = Depends(get_db)):
    if data.request_id:
        existing = db.scalar(select(MaterialRental).options(joinedload(MaterialRental.user),
            joinedload(MaterialRental.material)).where(MaterialRental.request_id == data.request_id))
        if existing:
            if existing.user_id != user.id:
                raise HTTPException(409, "此請求識別碼已被使用")
            return {"ok": True, "message": "此筆領用已完成", "rental": material_rental_json(existing),
                    "remaining_quantity": existing.material.quantity}
    material = db.get(Material, data.material_id)
    if not material:
        raise HTTPException(404, "找不到這項材料")
    if material.status != "active":
        raise HTTPException(409, "此材料目前無法領用")
    stock_before = material.quantity
    if stock_before < data.quantity:
        raise HTTPException(409, f"庫存不足，目前僅剩 {stock_before} 個")
    now = now_local()
    changed = db.execute(update(Material).where(Material.id == material.id,
        Material.status == "active", Material.quantity >= data.quantity).values(
        quantity=Material.quantity - data.quantity, updated_at=now))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "庫存已變更，請重新確認數量")
    status = "consumed" if material.material_type == "consumable" else "borrowed"
    rental = MaterialRental(user_id=user.id, material_id=material.id, quantity=data.quantity,
                            status=status, request_id=data.request_id, borrowed_at=now,
                            created_at=now, updated_at=now)
    db.add(rental)
    db.flush()
    db.refresh(material)
    audit(db, user.id, "material_borrow", f"material:{material.id}",
          {"rental_id": rental.id, "quantity": data.quantity,
           "stock_before": stock_before, "stock_after": material.quantity})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "此筆領用已送出，請重新整理紀錄")
    db.refresh(rental)
    result = {"ok": True, "message": "領用成功", "rental": material_rental_json(rental),
              "remaining_quantity": material.quantity}
    await broadcast({"type": "materials", "action": "material_borrow",
                     "material_id": material.id, "quantity": material.quantity})
    return result


@app.get("/api/material-rentals/mine")
def my_material_rentals(user: User = Depends(current_material_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(MaterialRental).options(joinedload(MaterialRental.user),
        joinedload(MaterialRental.material)).where(MaterialRental.user_id == user.id)
        .order_by(MaterialRental.borrowed_at.desc()).limit(100))
    return [material_rental_json(row) for row in rows]


def return_material_transaction(db: Session, rental: MaterialRental, actor_id: int):
    if rental.status != "borrowed":
        raise HTTPException(409, "此筆材料不是可歸還的借用中狀態")
    if rental.material.material_type != "returnable":
        raise HTTPException(409, "消耗型材料不需要歸還")
    stock_before = rental.material.quantity
    now = now_local()
    changed = db.execute(update(MaterialRental).where(MaterialRental.id == rental.id,
        MaterialRental.status == "borrowed").values(status="returned", returned_at=now, updated_at=now))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "此筆材料已經歸還或無法歸還")
    db.execute(update(Material).where(Material.id == rental.material_id).values(
        quantity=Material.quantity + rental.quantity, updated_at=now))
    db.flush()
    db.refresh(rental)
    db.refresh(rental.material)
    audit(db, actor_id, "material_return", f"material_rental:{rental.id}",
          {"material_id": rental.material_id, "quantity": rental.quantity,
           "stock_before": stock_before, "stock_after": rental.material.quantity})
    db.commit()
    return rental


@app.post("/api/material-rentals/{rental_id}/return")
async def return_my_material(rental_id: int, user: User = Depends(current_material_user),
                             db: Session = Depends(get_db)):
    rental = db.scalar(select(MaterialRental).options(joinedload(MaterialRental.user),
        joinedload(MaterialRental.material)).where(MaterialRental.id == rental_id))
    if not rental:
        raise HTTPException(404, "找不到這筆材料領用紀錄")
    if rental.user_id != user.id:
        raise HTTPException(403, "只能歸還自己借用的材料")
    return_material_transaction(db, rental, user.id)
    result = {"ok": True, "message": "材料已歸還", "rental": material_rental_json(rental),
              "remaining_quantity": rental.material.quantity}
    await broadcast({"type": "materials", "action": "material_return",
                     "material_id": rental.material_id, "quantity": rental.material.quantity})
    return result


@app.post("/api/rentals")
async def borrow(data: RentalIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.card_uid == clean_uid(data.card_uid), User.status == "active"))
    pc = db.get(Computer, data.computer_id)
    if not user:
        raise HTTPException(404, "找不到有效卡片")
    if not active_attendance(db, user.id):
        raise HTTPException(409, "借用前必須先簽到")
    if active_rental(db, user.id):
        raise HTTPException(409, "每人同時限借一台電腦")
    if not pc or pc.status != "available":
        raise HTTPException(409, "此電腦目前無法借用")
    rental = RentalRecord(computer_id=pc.id, user_id=user.id)
    pc.status = "in_use"
    db.add(rental)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "使用者或電腦已有進行中的租借")
    db.refresh(rental)
    result = {"ok": True, "message": f"已借用 {pc.id}", "rental": rental_json(rental), "computers": computers_json(db)}
    await broadcast({"type": "computers", **result})
    return result


@app.patch("/api/rentals/return")
async def return_computer(data: TapIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.card_uid == clean_uid(data.card_uid), User.status == "active"))
    rental = active_rental(db, user.id) if user else None
    if not rental:
        raise HTTPException(404, "此使用者沒有借用中的電腦")
    rental.returned_at = now_local()
    rental.computer.status = "available"
    db.commit()
    result = {"ok": True, "message": f"已歸還 {rental.computer_id}，使用 {rental_json(rental)['duration_minutes']} 分鐘",
              "rental": rental_json(rental), "computers": computers_json(db)}
    await broadcast({"type": "computers", **result})
    return result


@app.post("/api/admin/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.name == data.username, User.role == "admin", User.status == "active"))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "帳號或密碼錯誤")
    return {"token": new_token(user.id), "user": user_json(user)}


@app.post("/api/admin/logout")
def logout(authorization: Optional[str] = Header(default=None)):
    if authorization:
        TOKENS.pop(authorization.removeprefix("Bearer "), None)
    return {"ok": True}


@app.get("/api/admin/dashboard")
def dashboard(admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    start = datetime.combine(date.today(), time.min)
    present = db.scalar(select(func.count()).select_from(AttendanceRecord).where(AttendanceRecord.check_out_time.is_(None)))
    visits = db.scalar(select(func.count()).select_from(AttendanceRecord).where(AttendanceRecord.check_in_time >= start))
    return {"present_count": present, "today_visits": visits, "computers": computers_json(db)}


@app.get("/api/admin/users")
def list_users(admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    return [user_json(u) for u in db.scalars(select(User).order_by(User.created_at.desc()))]


@app.post("/api/admin/users")
def create_user(data: UserIn, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    if data.role not in {"member", "staff", "admin"}:
        raise HTTPException(422, "身分不正確")
    uid = clean_uid(data.card_uid) if data.card_uid else None
    user = User(name=data.name, phone=data.phone, role=data.role, card_uid=uid, status=data.status,
                password_hash=hash_password(data.password) if data.password else None)
    db.add(user)
    try:
        db.flush()
    except Exception:
        db.rollback()
        raise HTTPException(409, "卡片 UID 已存在")
    audit(db, admin.id, "create_user", f"user:{user.id}", user_json(user))
    db.commit()
    return user_json(user)


@app.put("/api/admin/users/{user_id}")
def update_user(user_id: int, data: UserIn, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "找不到使用者")
    if data.role not in {"member", "staff", "admin"}:
        raise HTTPException(422, "身分不正確")
    before = user_json(user)
    user.name, user.phone, user.role, user.status = data.name, data.phone, data.role, data.status
    user.card_uid = clean_uid(data.card_uid) if data.card_uid else None
    if data.password:
        user.password_hash = hash_password(data.password)
    audit(db, admin.id, "update_user", f"user:{user.id}", {"before": before, "after": user_json(user)})
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(409, "卡片 UID 已存在")
    return user_json(user)


@app.post("/api/admin/users/{user_id}/bind")
def start_binding(user_id: int, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "找不到使用者")
    binding.update(user_id=user_id, admin_id=admin.id, expires=now_local() + timedelta(seconds=60))
    audit(db, admin.id, "start_card_binding", f"user:{user_id}", {"expires": binding["expires"]})
    db.commit()
    return {"ok": True, "message": f"請在 60 秒內感應要綁定給 {user.name} 的卡片"}


@app.get("/api/admin/attendance")
def attendance_records(start: Optional[date] = None, end: Optional[date] = None, role: Optional[str] = None,
                       admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    query = select(AttendanceRecord).options(joinedload(AttendanceRecord.user)).order_by(AttendanceRecord.check_in_time.desc())
    if start: query = query.where(AttendanceRecord.check_in_time >= datetime.combine(start, time.min))
    if end: query = query.where(AttendanceRecord.check_in_time < datetime.combine(end + timedelta(days=1), time.min))
    if role: query = query.join(User).where(User.role == role)
    return [attendance_json(r) for r in db.scalars(query)]


@app.patch("/api/admin/attendance/{record_id}")
def edit_attendance(record_id: int, data: AttendanceEdit, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    row = db.get(AttendanceRecord, record_id)
    if not row: raise HTTPException(404, "找不到紀錄")
    before = {"in": dt(row.check_in_time), "out": dt(row.check_out_time), "flag": row.flag}
    if "check_in_time" in data.model_fields_set and data.check_in_time is not None:
        row.check_in_time = data.check_in_time
    if "check_out_time" in data.model_fields_set:
        row.check_out_time = data.check_out_time
    row.flag = "corrected"
    audit(db, admin.id, "correct_attendance", f"attendance:{row.id}", {"before": before, "note": data.note})
    db.commit()
    return attendance_json(row)


@app.get("/api/admin/rentals")
def rental_records(start: Optional[date] = None, end: Optional[date] = None,
                   admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    query = select(RentalRecord).options(joinedload(RentalRecord.user)).order_by(RentalRecord.borrowed_at.desc())
    if start: query = query.where(RentalRecord.borrowed_at >= datetime.combine(start, time.min))
    if end: query = query.where(RentalRecord.borrowed_at < datetime.combine(end + timedelta(days=1), time.min))
    return [rental_json(r) for r in db.scalars(query)]


@app.patch("/api/admin/rentals/{record_id}")
def edit_rental(record_id: int, data: RentalEdit, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    row = db.get(RentalRecord, record_id)
    if not row: raise HTTPException(404, "找不到紀錄")
    before = {"borrowed": dt(row.borrowed_at), "returned": dt(row.returned_at), "flag": row.flag}
    if "borrowed_at" in data.model_fields_set and data.borrowed_at is not None:
        row.borrowed_at = data.borrowed_at
    if "returned_at" in data.model_fields_set:
        row.returned_at = data.returned_at
        row.computer.status = "available" if data.returned_at else "in_use"
    row.flag = "corrected"
    audit(db, admin.id, "correct_rental", f"rental:{row.id}", {"before": before, "note": data.note})
    db.commit()
    return rental_json(row)


@app.patch("/api/admin/computers/{computer_id}")
async def set_computer(computer_id: str, data: ComputerPatch, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    pc = db.get(Computer, computer_id)
    if not pc or data.status not in {"available", "maintenance", "offline"}:
        raise HTTPException(422, "電腦或狀態不正確")
    if pc.status == "in_use": raise HTTPException(409, "使用中電腦請先強制歸還")
    before, pc.status = pc.status, data.status
    audit(db, admin.id, "computer_status", f"computer:{pc.id}", {"before": before, "after": data.status})
    db.commit()
    result = computers_json(db)
    await broadcast({"type": "computers", "computers": result})
    return result


@app.post("/api/admin/computers/{computer_id}/force-return")
async def force_return(computer_id: str, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    rental = db.scalar(select(RentalRecord).where(RentalRecord.computer_id == computer_id, RentalRecord.returned_at.is_(None)))
    if not rental: raise HTTPException(404, "此電腦沒有借用中紀錄")
    rental.returned_at, rental.flag, rental.computer.status = now_local(), "forced", "available"
    audit(db, admin.id, "force_return", f"rental:{rental.id}", {"computer_id": computer_id})
    db.commit()
    result = computers_json(db)
    await broadcast({"type": "computers", "computers": result})
    return result


@app.get("/api/admin/materials")
def list_materials(search: Optional[str] = None, category: Optional[str] = None,
                   active_only: bool = False, admin: User = Depends(current_admin),
                   db: Session = Depends(get_db)):
    query = select(Material).order_by(Material.category, Material.name, Material.specification)
    if category:
        query = query.where(Material.category == category)
    if search:
        keyword = f"%{search.strip()}%"
        query = query.where(or_(Material.name.ilike(keyword), Material.specification.ilike(keyword),
                                Material.location.ilike(keyword)))
    if active_only:
        query = query.where(Material.status == "active")
    return [material_json(row) for row in db.scalars(query)]


@app.get("/api/admin/materials/{material_id}")
def get_material(material_id: int, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    row = db.get(Material, material_id)
    if not row:
        raise HTTPException(404, "找不到材料")
    return material_json(row)


@app.post("/api/admin/materials")
def create_material(data: MaterialIn, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    if data.category not in {"resistor", "capacitor", "transistor"}:
        raise HTTPException(422, "材料類別不正確")
    if data.status not in {"active", "disabled"}:
        raise HTTPException(422, "材料狀態不正確")
    if data.material_type not in {"consumable", "returnable"}:
        raise HTTPException(422, "材料類型不正確")
    row = Material(**data.model_dump())
    db.add(row)
    db.flush()
    audit(db, admin.id, "create_material", f"material:{row.id}", material_json(row))
    db.commit()
    return material_json(row)


@app.put("/api/admin/materials/{material_id}")
def update_material(material_id: int, data: MaterialIn, admin: User = Depends(current_admin),
                    db: Session = Depends(get_db)):
    row = db.get(Material, material_id)
    if not row:
        raise HTTPException(404, "找不到材料")
    if data.category not in {"resistor", "capacitor", "transistor"}:
        raise HTTPException(422, "材料類別不正確")
    if data.status not in {"active", "disabled"}:
        raise HTTPException(422, "材料狀態不正確")
    if data.material_type not in {"consumable", "returnable"}:
        raise HTTPException(422, "材料類型不正確")
    before = material_json(row)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    row.updated_at = now_local()
    audit(db, admin.id, "update_material", f"material:{row.id}",
          {"before": before, "after": material_json(row)})
    db.commit()
    return material_json(row)


@app.delete("/api/admin/materials/{material_id}")
def disable_material(material_id: int, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    row = db.get(Material, material_id)
    if not row:
        raise HTTPException(404, "找不到材料")
    row.status = "disabled"
    row.updated_at = now_local()
    audit(db, admin.id, "disable_material", f"material:{row.id}", material_json(row))
    db.commit()
    return material_json(row)


@app.get("/api/admin/material-rentals")
def admin_material_rentals(start: Optional[date] = None, end: Optional[date] = None,
                           user_id: Optional[int] = None, material_id: Optional[int] = None,
                           status: Optional[str] = None, admin: User = Depends(current_admin),
                           db: Session = Depends(get_db)):
    query = select(MaterialRental).options(joinedload(MaterialRental.user),
        joinedload(MaterialRental.material)).order_by(MaterialRental.borrowed_at.desc())
    if start:
        query = query.where(MaterialRental.borrowed_at >= datetime.combine(start, time.min))
    if end:
        query = query.where(MaterialRental.borrowed_at < datetime.combine(end + timedelta(days=1), time.min))
    if user_id:
        query = query.where(MaterialRental.user_id == user_id)
    if material_id:
        query = query.where(MaterialRental.material_id == material_id)
    if status:
        query = query.where(MaterialRental.status == status)
    return [material_rental_json(row) for row in db.scalars(query)]


@app.post("/api/admin/material-rentals/{rental_id}/return")
async def admin_return_material(rental_id: int, admin: User = Depends(current_admin),
                                db: Session = Depends(get_db)):
    rental = db.scalar(select(MaterialRental).options(joinedload(MaterialRental.user),
        joinedload(MaterialRental.material)).where(MaterialRental.id == rental_id))
    if not rental:
        raise HTTPException(404, "找不到這筆材料領用紀錄")
    return_material_transaction(db, rental, admin.id)
    result = {"ok": True, "message": "材料已由管理員歸還", "rental": material_rental_json(rental),
              "remaining_quantity": rental.material.quantity}
    await broadcast({"type": "materials", "action": "material_return",
                     "material_id": rental.material_id, "quantity": rental.material.quantity})
    return result


@app.get("/api/admin/audit-logs")
def audit_logs(admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditLog).options(joinedload(AuditLog.admin)).order_by(AuditLog.created_at.desc()).limit(300))
    return [{"id": r.id, "admin": r.admin.name, "action": r.action, "target": r.target,
             "detail": r.detail, "created_at": dt(r.created_at)} for r in rows]


@app.get("/api/admin/settings")
def get_settings(admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    return {"closing_time": db.get(Setting, "closing_time").value}


@app.put("/api/admin/settings")
def update_settings(data: SettingPatch, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    try: time.fromisoformat(data.closing_time)
    except ValueError: raise HTTPException(422, "時間格式須為 HH:MM")
    setting = db.get(Setting, "closing_time")
    before, setting.value = setting.value, data.closing_time
    audit(db, admin.id, "update_setting", "setting:closing_time", {"before": before, "after": setting.value})
    db.commit()
    return {"closing_time": setting.value}


def report_rows(kind: str, month: str, db: Session) -> list[dict]:
    try: start = datetime.strptime(month, "%Y-%m")
    except ValueError: raise HTTPException(422, "月份格式須為 YYYY-MM")
    end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    if kind in {"staff", "members"}:
        role = "staff" if kind == "staff" else "member"
        rows = db.execute(select(User.name, func.count(AttendanceRecord.id),
            func.coalesce(func.sum(func.strftime('%s', AttendanceRecord.check_out_time) - func.strftime('%s', AttendanceRecord.check_in_time)), 0))
            .join(AttendanceRecord).where(User.role == role, AttendanceRecord.check_in_time >= start,
            AttendanceRecord.check_in_time < end).group_by(User.id)).all()
        return [{"姓名": name, "次數": count, "總時數": round(seconds / 3600, 2)} for name, count, seconds in rows]
    if kind == "computers":
        rows = db.execute(select(Computer.id, func.count(RentalRecord.id),
            func.coalesce(func.sum(func.strftime('%s', RentalRecord.returned_at) - func.strftime('%s', RentalRecord.borrowed_at)), 0))
            .outerjoin(RentalRecord, and_(Computer.id == RentalRecord.computer_id, RentalRecord.borrowed_at >= start,
            RentalRecord.borrowed_at < end)).group_by(Computer.id)).all()
        month_hours = (end - start).total_seconds() / 3600
        return [{"電腦": pc, "借用次數": count, "使用時數": round(seconds / 3600, 2),
                 "使用率%": round(seconds / 3600 / month_hours * 100, 2)} for pc, count, seconds in rows]
    raise HTTPException(404, "未知報表")


@app.get("/api/admin/reports/{kind}")
def report(kind: str, month: str = Query(...), admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    return report_rows(kind, month, db)


@app.get("/api/admin/reports/{kind}/csv")
def report_csv(kind: str, month: str = Query(...), admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    rows = report_rows(kind, month, db)
    output = io.StringIO()
    output.write('\ufeff')
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": f'attachment; filename="{kind}-{month}.csv"'})
