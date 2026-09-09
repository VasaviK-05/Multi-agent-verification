"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.routes import router
from app.utils.config import settings

app = FastAPI(title=settings.APP_NAME)
app.include_router(router)
