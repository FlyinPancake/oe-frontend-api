import secrets
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import Settings, get_settings
from app.dependencies import TokenRegistry
from app.errors import ApiError, api_error_handler
from app.routers import auth, catalog, developers, system, words
from app.store import Store

DESCRIPTION = """
Self-hosted copy of the practice API behind
[09 - JavaScript API](https://github.com/siposm/oktatas-frontend-szt-spec/wiki/09-javascript-api).

Data lives in memory and resets on restart or on `GET /reset`.
Deleting skills and jobs needs a token from `POST /login` (`johndoe` / `johndoe123`).
"""


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.store = Store(settings.data_dir)
        app.state.tokens = TokenRegistry(ttl_seconds=settings.token_ttl_seconds)
        yield

    app = FastAPI(
        title=settings.title,
        version=settings.version,
        description=DESCRIPTION,
        lifespan=lifespan,
        openapi_tags=[
            {"name": "words", "description": "Exercises 1 to 3"},
            {"name": "developers", "description": "Exercises 4 and 5.1"},
            {"name": "skills", "description": "Exercise 5.2"},
            {"name": "jobs", "description": "Exercise 5.3"},
            {"name": "auth"},
            {"name": "system"},
        ],
    )
    app.dependency_overrides[get_settings] = lambda: settings

    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID") or secrets.token_hex(8)
        request.state.started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - request.state.started) * 1000
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Process-Time"] = f"{elapsed_ms:.3f}ms"
        return response

    app.add_exception_handler(ApiError, api_error_handler)

    for router in (
        words.router,
        developers.router,
        catalog.skills,
        catalog.jobs,
        auth.router,
        system.router,
    ):
        app.include_router(router)

    return app


app = create_app()
