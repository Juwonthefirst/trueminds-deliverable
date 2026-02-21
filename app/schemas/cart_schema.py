from app.models import BaseCartItem, Food


class CartItemCreate(BaseCartItem):
    food_id: int
    side_protein: list[int]
    extra_side: list[int]


class CartItemRead(BaseCartItem):
    food: Food
    side_protein: list[Food]
    extra_side: list[Food]
