from operator import contains
from typing import cast
from fastapi import HTTPException
from sqlalchemy import ColumnElement, exc
from sqlmodel import Session, select, delete
from app.models import CartItem, Food, User
from app.schemas.cart_schema import CartItemCreate


class CartServices:
    def __init__(self, db: Session, user: User) -> None:
        self.db = db
        self.user = user

    def get_cart_item(
        self, food_id: int, side_protein: list[int], extra_side: list[int]
    ):
        statement = (
            select(CartItem)
            .where(
                CartItem.buyer_id == self.user.id,
                CartItem.food_id == food_id,
            )
            .join(CartItem.side_protein)
            .where(contains(CartItem.side_protein, side_protein))
            .join(CartItem.extra_side)
            .where(contains(CartItem.extra_side, extra_side))
        )
        return self.db.exec(statement).first()

    def add_to_cart(self, cart_item: CartItemCreate) -> CartItem:
        try:
            cart_item_in_db = self.get_cart_item(
                cart_item.food_id, cart_item.side_protein, cart_item.extra_side
            )
            if cart_item_in_db:
                cart_item_in_db.quantity += cart_item.quantity
                cart_item_in_db.save(self.db)
                return cart_item_in_db

            db_cart_item = CartItem(**cart_item.model_dump(), buyer_id=self.user.id)
            db_cart_item.save(self.db)
            return db_cart_item

        except exc.IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail="The new cart item is conflicting with another in the db",
            )
        except exc.SQLAlchemyError as e:
            self.db.rollback()
            print(e)
            raise HTTPException(
                status_code=500, detail="Something went wrong at our end"
            )
        except Exception as e:
            print(f"Error fetching cart: {e}")
            raise HTTPException(
                status_code=500, detail="Something went wrong at our end"
            )

    def get_active_cart(self):
        try:
            on_clause = cast(ColumnElement[bool], CartItem.food_id == Food.id)
            statement = (
                select(CartItem, Food)
                .join(Food, on_clause)
                .where(CartItem.buyer_id == self.user.id)
            )
            return self.db.exec(statement).all()

        except exc.SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=500, detail="Something went wrong at our end"
            )
        except Exception as e:
            print(f"Error fetching cart: {e}")
            return []

    def clear_cart(self):
        try:
            on_clause = cast(ColumnElement[bool], CartItem.buyer_id == self.user.id)
            statement = delete(CartItem).where(on_clause)
            self.db.exec(statement)
            self.db.commit()
            return True
        except exc.SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=500, detail="Something went wrong at our end"
            )
        except Exception as e:
            print(f"Error clearing cart: {e}")
            return False
