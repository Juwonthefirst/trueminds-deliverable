from typing import cast
from sqlalchemy import ColumnElement
from sqlmodel import Session, select, delete
from app.models import CartItem, Food, User


class CartServices:
    def __init__(self, db: Session, user: User) -> None:
        self.db = db
        self.user = user

    def get_active_cart(self):
        try:
            on_clause = cast(ColumnElement[bool], CartItem.food_id == Food.id)
            statement = (
                select(CartItem, Food)
                .join(Food, on_clause)
                .where(CartItem.user_id == self.user.id)
            )
            return self.db.exec(statement).all()
        except Exception as e:
            print(f"Error fetching cart: {e}")
            return []

    def clear_cart(self):
        try:
            on_clause = cast(ColumnElement[bool], CartItem.user_id == self.user.id)
            statement = delete(CartItem).where(on_clause)
            self.db.exec(statement)
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error clearing cart: {e}")
            return False
