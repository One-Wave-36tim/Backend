from fastapi import FastAPI

from app.router import router

app = FastAPI(title="Backend")
app.include_router(router)
