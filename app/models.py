from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel, Session
from typing import Optional
from sqlalchemy.orm import Mapped


## Base models for shared attributes and methods
class DBModelBase(SQLModel):
    def save(self, db: Session):
        db.add(self)
        db.commit()
        db.refresh(self)
        return self

    def delete(self, db: Session):
        db.delete(self)
        db.commit()

    def update(self, db: Session, **kwargs):
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)
        self.save(db)
        return self


## User model
class BaseUser(SQLModel):
    email: EmailStr = Field(unique=True, index=True)
    phone_number: int = Field(unique=True, index=True)
    referral_code: str | None
    is_admin: bool | None = Field(default=False)


## Food model
class BaseFood(SQLModel):
    name: str
    description: str
    price: int
    image_url: str
    category: str
    available_quatity: int


## Link models
class CartItem(DBModelBase, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    food_id: int = Field(foreign_key="food.id", primary_key=True)
    quantity: int
    special_instructions: Optional[str] = None


# class OrderItem(DBModelBase, table=True):
#     order_id: int = Field(foreign_key="order.id", primary_key=True)
#     food_id: int = Field(foreign_key="food.id", primary_key=True)
#     quantity: int
#     special_instructions: Optional[str] = None
#     price_at_order: int
#     ordered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


## Main models
class User(DBModelBase, BaseUser, table=True):
    id: int | None = Field(default=None, primary_key=True)
    password: str
    # orders: list[Order] = Relationship(back_populates="user")
    cart: Mapped[list[Food]] = Relationship(link_model=CartItem)


class Food(DBModelBase, BaseFood, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cart_users: list[User] = Relationship(link_model=CartItem)
    # orders: Mapped[list[Order]] = Relationship(link_model=OrderItem)


# class BaseOrder(SQLModel):
#     pass


# class OrderStatus(str, Enum):
#     PENDING = "pending"
#     CONFIRMED = "confirmed"
#     PREPARING = "preparing"
#     OUT_FOR_DELIVERY = "out_for_delivery"
#     COMPLETED = "completed"
#     CANCELLED = "cancelled"


# class Order(DBModelBase, BaseOrder, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     user_id: int = Field(foreign_key="user.id")
#     user: User = Relationship(back_populates="orders")
#     items: list[Food] = Relationship(link_model=OrderItem)
#     status: OrderStatus = Field(default=OrderStatus.PENDING)
#     ordered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
