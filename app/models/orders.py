from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel

from app.models.core import DBModelBase

# from app.models.foods import Food
# from app.models.users import User


class LinkItem(SQLModel):
    food_id: int = Field(foreign_key="food.id", primary_key=True)
    food: "Food" = Relationship(back_populates="owners")
    side_protein_id: Optional[int] = Field(foreign_key="food.id")
    side_protein: "Food" = Relationship()
    extra_side_id: Optional[int] = Field(foreign_key="food.id")
    extra_side: "Food" = Relationship()

    quantity: int
    special_instructions: Optional[str]


class CartItem(DBModelBase, LinkItem, table=True):
    owner_id: int = Field(foreign_key="user.id", primary_key=True)
    owner: "User" = Relationship(back_populates="cart_items")


class BaseOrder(SQLModel):
    user_id: int = Field(foreign_key="user.id")


class Order(DBModelBase, BaseOrder, table=True):
    id: int | None = Field(primary_key=True)
    user: "User" = Relationship(back_populates="orders")


class OrderItem(DBModelBase, LinkItem, table=True):
    order_id: int = Field(foreign_key="order.id", primary_key=True)
    order: "Order" = Relationship(back_populates="order_items")
    total_price: int
    ordered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
