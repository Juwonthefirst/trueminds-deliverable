import os
from pydantic_settings import BaseSettings


class Settigs(BaseSettings):
    authjwt_secret_key: str = os.getenv("SECRET_KEY", "")


settings = Settigs()
