import logging

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routes import router

load_dotenv()  # loads DB_DSN from a local .env file if present
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AS400 API Wrapper",
    version="0.1.0",
    description="Experimental prototype: exposing IBM i (Db2 for i) data and "
    "SQL-registered programs as REST APIs. Not validated on a live IBM i.",
)
app.include_router(router)
