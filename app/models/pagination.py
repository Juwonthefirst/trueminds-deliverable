from typing import Generic, Sequence, TypeVar
from pydantic import BaseModel

result_type = TypeVar("result_type")


class PaginationResponse(BaseModel, Generic[result_type]):
    next: str | None
    prev: str | None
    count: int
    result: Sequence[result_type]
