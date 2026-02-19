from app.models import BaseUser


class UserCreate(BaseUser):
    password: str


class UserPublic(BaseUser):
    id: int
