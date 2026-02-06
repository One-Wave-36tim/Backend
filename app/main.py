from fastapi import FastAPI

from app.db.session import Base, get_engine
from app.router import router

app = FastAPI(title="Backend")
app.include_router(router)


@app.on_event("startup")
def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())
