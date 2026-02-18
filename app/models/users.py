from __future__ import annotations

from typing import TYPE_CHECKING
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

from app.models.core import DBModelBase
from app.models.orders import CartItem


class BaseUser(SQLModel):
    email: EmailStr = Field(unique=True, index=True)
    phone_number: int = Field(unique=True, index=True)
    referral_code: str | None
    is_admin: bool | None = Field(default=False)


class User(DBModelBase, BaseUser, table=True):
    id: int | None = Field(default=None, primary_key=True)
    password: str
    orders: list["Order"] = Relationship(back_populates="user")
    cart: list["Food"] = Relationship(link_model=CartItem, back_populates="owners")


class UserCreate(BaseUser):
    password: str


class UserPublic(BaseUser):
    id: int
