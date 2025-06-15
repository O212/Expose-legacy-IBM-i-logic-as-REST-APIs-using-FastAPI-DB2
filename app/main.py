from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="AS400 API Wrapper")
app.include_router(router)
