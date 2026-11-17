import resource
import secrets
import time
from datetime import datetime

from fastapi import APIRouter, Request

from app.dependencies import SettingsDep, StoreDep
from app.models import (
    ResetResponse,
    StatusDemo,
    StatusHealth,
    StatusMeta,
    StatusPerformance,
    StatusResponse,
)

router = APIRouter(tags=["system"])


@router.get("/status", summary="Demo status response")
async def get_status(request: Request, settings: SettingsDep, store: StoreDep) -> StatusResponse:
    peak_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return StatusResponse(
        meta=StatusMeta(
            api_version=settings.version,
            environment=settings.environment,
            server_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            request_id=request.state.request_id,
        ),
        health=StatusHealth(database=bool(store.words), cache=True),
        performance=StatusPerformance(
            response_time_ms=round((time.perf_counter() - request.state.started) * 1000, 3),
            memory_usage=peak_kib * 1024,
            memory_peak=peak_kib * 1024,
        ),
        demo=StatusDemo(random_token=secrets.token_hex(6)),
    )


@router.get("/reset", operation_id="reset_get", summary="Restore the seed data")
@router.post("/reset", operation_id="reset_post", summary="Restore the seed data")
async def reset(store: StoreDep) -> ResetResponse:
    store.reset()
    return ResetResponse(
        message="All data has been reset to the default state.",
        developers=len(store.developers),
        skills=len(store.skills),
        jobs=len(store.jobs),
        words=len(store.words),
    )
