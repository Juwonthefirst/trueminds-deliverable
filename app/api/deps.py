from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.database import SessionDep

security = HTTPBasic()

CredentialsDep = Annotated[HTTPBasicCredentials, Depends(security)]

def get_current_user(credentials: CredentialsDep, session: SessionDep):
    user = 