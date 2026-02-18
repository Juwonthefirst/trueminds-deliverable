from fastapi import APIRouter

from app.core.database import SessionDep


router = APIRouter(prefix="/order", tags=["orders"])


@router.post("/")
def make_order(session: SessionDep):
    pass
