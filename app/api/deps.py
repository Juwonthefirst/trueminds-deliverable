from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.database import SessionDep
from app.models import User
from app.services.auth_services import (
    AuthFailedError,
    AuthServices,
    InvalidCredentialError,
)

security = HTTPBasic()

CredentialsDep = Annotated[HTTPBasicCredentials, Depends(security)]


def get_current_user(credentials: CredentialsDep, session: SessionDep):
    auth_service = AuthServices(session)

    try:
        user_id = int(credentials.username)
    except ValueError:
        raise InvalidCredentialError("user_id")

    user = session.get(User, user_id)
    if user is None:
        raise AuthFailedError()
    if not auth_service.verify_password(credentials.password, user.password):
        raise AuthFailedError()
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
