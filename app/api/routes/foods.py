from sqlite3 import IntegrityError
from fastapi import APIRouter, HTTPException, Query, Request
from sqlmodel import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionDep
from app.models import Food
from app.schemas.foods_schema import FoodCreate
from app.schemas.pagination import PaginationResponse


router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("/")
async def get_foods(
    request: Request,
    session: SessionDep,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginationResponse[Food]:

    base_url = request.base_url
    foods = session.exec(select(Food).offset(offset).limit(limit)).all()
    no_of_foods = len(foods)
    next = (
        f"{base_url}?limit={10}&offset={offset + 1}" if no_of_foods == limit else None
    )
    prev = f"{base_url}?limit={10}&offset={(offset - 1)}" if offset > 0 else None
    return PaginationResponse(next=next, prev=prev, count=len(foods), result=foods)


@router.post("/")
# check if the user is an admin before allowing the user to create a food
async def create_food(food: FoodCreate, session: SessionDep) -> Food:
    db_food = Food.model_validate(food)
    try:
        db_food.save(session)
        return db_food

    except IntegrityError as e:
        session.rollback()
        raise HTTPException(
            status_code=409, detail=f"Food with this name already exists: {e}"
        )

    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create food: {e}")
