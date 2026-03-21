import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mirror.api.config_store import initialize_config_db
from mirror.api.routes import router as mirror_router
from mirror.api.settings import get_cors_origins
from mirror.api.report_routes import router as report_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_config_db()
    yield


app = FastAPI(
    title="Mirror API",
    description="HTTP API for worksheet parsing and exercise generation.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mirror_router)

# report crap
app.include_router(report_router)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "name": "mirror-api",
        "docs": "/docs",
        "health": "/api/health",
    }
