from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.hierarchy import router as hierarchy_router
from app.config import settings

app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(hierarchy_router)
