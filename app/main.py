from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import cart, foods, users
from app.core.database import create_db_and_tables


app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
app.include_router(foods.router)
app.include_router(users.router)
app.include_router(cart.router)


@app.on_event("startup")  # type: ignore
async def startup_event():
    create_db_and_tables()
