from typing import Optional

from app.models import BaseCartItem, Food


class CartItemCreate(BaseCartItem):
    food_id: int
    side_protein_id: Optional[int]
    extra_side_id: Optional[int]


class CartItemRead(BaseCartItem):
    food: Food
    side_protein: Food | None
    extra_side: Food | None
