from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def now_local() -> datetime:
    return datetime.now().replace(microsecond=0)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    role: Mapped[str] = mapped_column(String(20))
    card_uid: Mapped[Optional[str]] = mapped_column(String(80), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    password_hash: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    check_in_time: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    check_out_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    type: Mapped[str] = mapped_column(String(30))
    flag: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    user: Mapped[User] = relationship()


class Computer(Base):
    __tablename__ = "computers"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default="available")


class RentalRecord(Base):
    __tablename__ = "rental_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    computer_id: Mapped[str] = mapped_column(ForeignKey("computers.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    borrowed_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    flag: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    user: Mapped[User] = relationship()
    computer: Mapped[Computer] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(80))
    target: Mapped[str] = mapped_column(String(120))
    detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    admin: Mapped[User] = relationship()


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(String(200))


class Material(Base):
    __tablename__ = "materials"
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    specification: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    quantity: Mapped[int] = mapped_column(default=0)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    material_type: Mapped[str] = mapped_column(String(20), default="consumable")
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=now_local, onupdate=now_local)


class MaterialRental(Base):
    __tablename__ = "material_rentals"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), index=True)
    quantity: Mapped[int] = mapped_column()
    borrowed_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="borrowed")
    request_id: Mapped[Optional[str]] = mapped_column(String(80), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)
    user: Mapped[User] = relationship()
    material: Mapped[Material] = relationship()


class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(20), index=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mpn: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    specs: Mapped[dict] = mapped_column(JSON, default=dict)
    total_quantity: Mapped[int] = mapped_column(default=0)
    safe_stock_level: Mapped[int] = mapped_column(default=0)
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    current_borrower: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    borrowed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expected_return_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)
    borrower: Mapped[Optional[User]] = relationship(foreign_keys=[current_borrower])


class Slot(Base):
    __tablename__ = "slots"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    cabinet: Mapped[str] = mapped_column(String(20), index=True)
    parent_slot_id: Mapped[Optional[int]] = mapped_column(ForeignKey("slots.id"), nullable=True)
    capacity_hint: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    parent: Mapped[Optional["Slot"]] = relationship(remote_side="Slot.id")


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint("item_id", "slot_id", "batch_no", name="uq_inventory_item_slot_batch"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("slots.id"), index=True)
    quantity: Mapped[int] = mapped_column(default=0)
    batch_no: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    received_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    item: Mapped[Item] = relationship()
    slot: Mapped[Slot] = relationship()


class ToolRental(Base):
    __tablename__ = "tool_rentals"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    borrowed_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    expected_return_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="borrowed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)
    item: Mapped[Item] = relationship()
    user: Mapped[User] = relationship()
