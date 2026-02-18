from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel

from app.models.core import DBModelBase


if TYPE_CHECKING:
    from app.models.foods import Food
    from app.models.users import User


class LinkItem(SQLModel):
    food_id: Optional[int] = Field(
        default=None, foreign_key="food.id", primary_key=True
    )
    side_protein_id: Optional[int] = Field(foreign_key="food.id")
    side_protein: "Food" = Relationship()
    extra_side_id: Optional[int] = Field(foreign_key="food.id")
    extra_side: "Food" = Relationship()

    quantity: int
    special_instructions: Optional[str]


class CartItem(DBModelBase, LinkItem, table=True):
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
