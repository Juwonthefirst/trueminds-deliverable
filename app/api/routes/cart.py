from fastapi import APIRouter, HTTPException

from app.core.database import SessionDep
from app.models import User
from app.services.cart_services import CartServices


router = APIRouter(tags=["cart"])


@router.post("{user_id}/cart/clear")
def clear_cart(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usernot found")
    cart_service = CartServices(session, user)
    is_cleared = cart_service.clear_cart()

    if not is_cleared:
        raise HTTPException(status_code=500, detail="Failed to clear cart")

    return {"message": "Cart cleared successfully"}
