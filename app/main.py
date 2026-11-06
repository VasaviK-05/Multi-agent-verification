"""FastAPI application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.feedback_routes import router as feedback_router
from app.utils.config import settings
from app.database.execution_recovery import (
    inspect_and_recover_incomplete_executions,
)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run database recovery before accepting application requests."""

    try:
        recovery_results = await asyncio.to_thread(
            inspect_and_recover_incomplete_executions
        )

        app.state.recovery_results = recovery_results

        logger.info(
            "Startup recovery completed. "
            "%d incomplete executions were recovered.",
            len(recovery_results),
        )

    except Exception:
        logger.exception(
            "Startup recovery failed. Application startup aborted."
        )
        raise

    yield


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(feedback_router)
app.include_router(router)
