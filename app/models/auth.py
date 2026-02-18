from typing import TypedDict
from pydantic import BaseModel


class OTP(BaseModel):
    otp: str


class SignupSessionData(TypedDict):
    user: str
    attempts: int
    otp_hash: str
