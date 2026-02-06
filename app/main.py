from fastapi import FastAPI

from app.api.api import api_router

app = FastAPI(title="Backend")
app.include_router(api_router)
