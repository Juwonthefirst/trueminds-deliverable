from __future__ import annotations

from typing import TYPE_CHECKING
from sqlmodel import Relationship, SQLModel, Field

from app.models.core import DBModelBase
from app.models.link_models import CartItem

if TYPE_CHECKING:
    from app.models.users import User


class BaseFood(SQLModel):
    name: str
    description: str
    price: int
    image_url: str
    category: str
    available_quatity: int


class Food(DBModelBase, BaseFood, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owners: list["User"] = Relationship(link_model=CartItem, back_populates="food")


class FoodCreate(BaseFood):
    pass
