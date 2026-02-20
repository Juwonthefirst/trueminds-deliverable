import secrets
from fastapi import HTTPException
from pydantic import EmailStr
from sqlmodel import select
from argon2 import PasswordHasher
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.database import SessionDep
from app.models import User
from app.schemas.auth_schema import SignupSessionData
from app.core.cache import cache
from app.schemas.users_schema import UserCreate

ph = PasswordHasher()


class AuthFailedError(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="Invalid Authentication credentials")


class InvalidCredentialError(HTTPException):
    def __init__(self, credential_name: str):
        super().__init__(status_code=401, detail=f"Invalid {credential_name}")


class AuthServices:
    def __init__(self, db: SessionDep):
        self.db = db

    def verify_ceridentials(self, email: EmailStr, phone_number: int):
        is_email_in_use = (
            self.db.exec(select(User.id).where(User.email == email)).first() is not None
        )
        is_phone_number_in_use = (
            self.db.exec(
                select(User.id).where(User.phone_number == phone_number)
            ).first()
            is not None
        )
        if is_email_in_use:
            raise HTTPException(status_code=409, detail="This email is already in use")
        if is_phone_number_in_use:
            raise HTTPException(
                status_code=409, detail="This phone number is already in use"
            )

    async def create_user_verification_session(
        self, user: UserCreate, otp_hash: str, session_duration: int
    ):
        session_id = secrets.token_urlsafe(32)
        session_data: SignupSessionData = {
            "user": user.model_dump_json(),
            "attempts": 0,
            "otp_hash": otp_hash,
        }

        await cache.set_hash(
            f"signup_session:{session_id}",
            mapping=session_data,
            expiry_time=session_duration,
        )
        return session_id

    async def get_user_verification_session(self, session_id: str):
        session_data = await cache.get_hash(f"signup_session:{session_id}")
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        return SignupSessionData(**session_data)

    async def increase_session_validation_attempts(self, session_id: str):
        return await cache.increase_hash_field(
            f"signup_session:{session_id}", "attempts"
        )

    async def delete_user_verification_session(self, session_id: str):
        await cache.delete(f"signup_session:{session_id}")

    def hash_password(self, password: str) -> str:
        return ph.hash(password)

    def verify_password(self, password: str, hashed_password: str):
        return ph.verify(hashed_password, password)

    async def create_user(self, user_data: dict) -> User:
        try:
            self.verify_ceridentials(user_data["email"], user_data["phone_number"])
            user = User.model_validate(user_data)
            user.password = self.hash_password(user.password)
            user.save(self.db)
            return user
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=409, detail=f"Food with this name already exists: {e}"
            )

        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create food: {e}")
