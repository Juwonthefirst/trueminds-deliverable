from datetime import datetime, timezone
from enum import Enum
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel, Session
from typing import Optional


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
    referral_code: Optional[str]
    is_admin: Optional[bool] = Field(default=False)


## Food model
class BaseFood(SQLModel):
    name: str
    description: str
    price: int
    image_url: str
    category: str
    available_quatity: int


## Main models
class User(DBModelBase, BaseUser, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
    orders: list["Order"] = Relationship(back_populates="user")
    cart_link: list["CartItem"] = Relationship(back_populates="buyer")


class Food(DBModelBase, BaseFood, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    buyer_link: list["CartItem"] = Relationship(
        back_populates="food",
        sa_relationship_kwargs={"foreign_keys": "[CartItem.food_id]"},
    )
    cart_side_protein_link: list["CartItem"] = Relationship(
        back_populates="side_protein",
        sa_relationship_kwargs={"foreign_keys": "[CartItem.side_protein_id]"},
    )
    cart_extra_side_link: list["CartItem"] = Relationship(
        back_populates="extra_side",
        sa_relationship_kwargs={"foreign_keys": "[CartItem.extra_side_id]"},
    )
    order_side_protein_link: list["OrderItem"] = Relationship(
        back_populates="side_protein",
        sa_relationship_kwargs={"foreign_keys": "[OrderItem.side_protein_id]"},
    )
    order_extra_side_link: list["OrderItem"] = Relationship(
        back_populates="extra_side",
        sa_relationship_kwargs={"foreign_keys": "[OrderItem.extra_side_id]"},
    )
    order_link: list["OrderItem"] = Relationship(
        back_populates="food",
        sa_relationship_kwargs={"foreign_keys": "[OrderItem.food_id]"},
    )


## Link models
class BaseCartItem(SQLModel):
    quantity: int
    special_instructions: Optional[str]


class CartItem(DBModelBase, BaseCartItem, table=True):
    food_id: int = Field(foreign_key="food.id", primary_key=True)
    side_protein_id: Optional[int] = Field(default=None, foreign_key="food.id")
    extra_side_id: Optional[int] = Field(default=None, foreign_key="food.id")
    buyer_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    buyer: User = Relationship(back_populates="cart_link")
    food: Food = Relationship(
        back_populates="buyer_link",
        sa_relationship_kwargs={"foreign_keys": "[CartItem.food_id]"},
    )
    side_protein: Food = Relationship(
        back_populates="cart_side_protein_link",
        sa_relationship_kwargs={"foreign_keys": "[CartItem.side_protein_id]"},
    )
    extra_side: Food = Relationship(
        back_populates="cart_extra_side_link",
        sa_relationship_kwargs={"foreign_keys": "[CartItem.extra_side_id]"},
    )


class OrderItem(DBModelBase, table=True):
    order_id: int = Field(foreign_key="order.id", primary_key=True)
    order: "Order" = Relationship(back_populates="food_link")

    food_id: int = Field(foreign_key="food.id", primary_key=True)
    food: Food = Relationship(
        back_populates="order_link",
        sa_relationship_kwargs={"foreign_keys": "[OrderItem.food_id]"},
    )

    side_protein_id: Optional[int] = Field(default=None, foreign_key="food.id")
    side_protein: Food = Relationship(
        back_populates="order_side_protein_link",
        sa_relationship_kwargs={"foreign_keys": "[OrderItem.side_protein_id]"},
    )

    extra_side_id: Optional[int] = Field(default=None, foreign_key="food.id")
    extra_side: Food = Relationship(
        back_populates="order_extra_side_link",
        sa_relationship_kwargs={"foreign_keys": "[OrderItem.extra_side_id]"},
    )

    quantity: int
    special_instructions: Optional[str]

    price_at_order: int
    ordered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BaseOrder(SQLModel):
    pass


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(DBModelBase, BaseOrder, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="orders")
    food_link: list["OrderItem"] = Relationship(back_populates="order")
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    ordered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
