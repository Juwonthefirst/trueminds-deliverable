import json
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Cookie, Response

from app.core.database import SessionDep
from app.models.auth import OTP
from app.models.users import UserPublic, UserCreate
from app.services.auth import AuthServices
from app.services.email import EmailServices
from app.services.otp import (
    OTPServices,
    OTPValidationAttemptsExceededError,
    OTPVerificationError,
)
from app.core.utils import is_prod_enviroment

router = APIRouter(tags=["auth"])


@router.post("/signup/")
async def signup(
    user: UserCreate,
    session: SessionDep,
    response: Response,
    background_tasks: BackgroundTasks,
):
    auth_service = AuthServices(session)
    auth_service.verify_ceridentials(user.email, user.phone_number)
    otp, otp_hash = OTPServices.generate_otp()
    session_id = await auth_service.create_user_verification_session(
        user=user, otp_hash=otp_hash, session_duration=OTPServices.OTP_EXPIRY_TIME
    )

    background_tasks.add_task(EmailServices.send_otp_mail, to=user.email, otp=otp)

    response.set_cookie(
        key="signup_session_id",
        value=session_id,
        httponly=True,
        secure=is_prod_enviroment,
        samesite="none" if is_prod_enviroment else "lax",
        max_age=OTPServices.OTP_EXPIRY_TIME,
    )
    return {
        "message": "OTP sent to your email address",
        "signup_session_id": session_id,
    }


@router.post("/verify/", response_model=UserPublic)
async def verify_otp(
    otp: OTP,
    signup_session_id: Annotated[str, Cookie()],
    session: SessionDep,
    response: Response,
):
    auth_service = AuthServices(session)
    session_data = await auth_service.get_user_verification_session(signup_session_id)
    is_otp_valid = OTPServices.verify_otp(otp.otp, session_data["otp_hash"])
    if not is_otp_valid:
        no_of_attempts = await auth_service.increase_session_validation_attempts(
            signup_session_id
        )
        if no_of_attempts >= OTPServices.MAX_ATTEMPTS:
            await auth_service.delete_user_verification_session(signup_session_id)
            raise OTPValidationAttemptsExceededError()
        raise OTPVerificationError()
    user_data = json.loads(session_data["user"])
    user = await auth_service.create_user(user_data)

    response.delete_cookie(key="signup_session_id")
    await auth_service.delete_user_verification_session(signup_session_id)
    return user
