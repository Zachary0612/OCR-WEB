"""V1 router registry.

This module is the single wiring entrypoint for API routers.
During migration we still import legacy router modules from ``app.api`` and
compose them here, so ``main.py`` no longer depends on route file details.
"""

from fastapi import FastAPI

from app.api.archives import router as archives_router
from app.api.auth_routes import router as auth_router
from app.api.batches import router as batches_router
from app.api.evaluation import router as evaluation_router
from app.api.files import router as files_router
from app.api.qa import router as qa_router
from app.api.tasks import router as tasks_router


V1_ROUTERS = (
    auth_router,
    tasks_router,
    archives_router,
    batches_router,
    qa_router,
    evaluation_router,
    files_router,
)


def include_v1_routers(app: FastAPI) -> None:
    """Attach all public v1 routers to the FastAPI app."""
    for router in V1_ROUTERS:
        app.include_router(router)

