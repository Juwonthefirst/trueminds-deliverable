from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUserDep
from app.core.database import SessionDep
from app.schemas.cart_schema import CartItemCreate, CartItemRead
from app.services.cart_services import CartServices


router = APIRouter(prefix="/cart", tags=["cart"])


@router.post("/", response_model=CartItemRead)
def add_to_cart(
    cart_item: CartItemCreate, session: SessionDep, current_user: CurrentUserDep
):
    cart_service = CartServices(session, current_user)
    new_cart_item = cart_service.add_to_cart(cart_item)
    return new_cart_item


@router.delete("/clear/")
def clear_cart(session: SessionDep, current_user: CurrentUserDep):
    cart_service = CartServices(session, current_user)
    is_cleared = cart_service.clear_cart()
    if not is_cleared:
        raise HTTPException(status_code=500, detail="Failed to clear cart")

    return {"message": "Cart cleared successfully"}
