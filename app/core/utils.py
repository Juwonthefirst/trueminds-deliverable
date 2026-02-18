import os
from dotenv import load_dotenv


def load_enviroment_variables():
    load_dotenv()
    is_prod_enviroment = os.getenv("ENVIROMENT") == "production"
    if is_prod_enviroment:
        load_dotenv(".env.production", override=True)
        load_dotenv(".env.production.local", override=True)
    else:
        load_dotenv(".env.local", override=True)


is_prod_enviroment = os.getenv("ENVIROMENT") == "production"
