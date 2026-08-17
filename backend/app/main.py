from fastapi import FastAPI

from app.api.evaluation_questions import router as evaluation_questions_router
from app.api.health import router as health_router
from app.api.hierarchy import router as hierarchy_router
from app.api.leaders import router as leaders_router
from app.config import settings

app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(hierarchy_router)
app.include_router(leaders_router)
app.include_router(evaluation_questions_router)
