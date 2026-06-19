import logging
import sys

from app.base.log_formatter import RequestIdFormatter

root_logger = logging.getLogger()
root_logger.handlers.clear()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(RequestIdFormatter("%(levelname)s %(name)s - %(message)s"))
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

from contextlib import asynccontextmanager
from sqlalchemy import text

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.base.server import AppServer
from app.core.config import settings
from app.database.session import engine
from app.database.models import Base
from app.models.schemas import HealthResponse
from app.routes.auth import router as auth_router
from app.routes.resume import router as resume_router
from app.routes.chat import router as chat_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created")
    yield
    logger.info("Shutting down...")
    engine.dispose()


app = AppServer(
    title=settings.app_name,
    version=settings.app_version,
    description="Resume Analyser AI — Upload, parse, and analyse resumes with AI-powered feedback",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(chat_router)


@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to Resume Analyser AI", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
    )
