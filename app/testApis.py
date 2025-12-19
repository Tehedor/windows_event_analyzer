# main.py

from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="Window Query Engine",
    version="1.0",
)

app.include_router(router)
