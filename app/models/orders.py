from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel

from app.models.core import DBModelBase
from app.models.link_models import LinkItem


class BaseOrder(SQLModel):
    user_id: int = Field(foreign_key="user.id")


class Order(DBModelBase, BaseOrder, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user: "User" = Relationship(back_populates="orders")
    order_items: list["OrderItem"] = Relationship(back_populates="order")


class OrderItem(DBModelBase, LinkItem, table=True):
    order_id: int = Field(foreign_key="order.id", primary_key=True)
    order: "Order" = Relationship(back_populates="order_items")
    total_price: int
    ordered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
