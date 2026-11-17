from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """An error whose JSON body is sent to the client as-is.

    The original API uses a different error body per endpoint group, so each
    raise site passes the exact body it needs.
    """

    def __init__(
        self, status_code: int, body: dict[str, Any], headers: dict[str, str] | None = None
    ) -> None:
        self.status_code = status_code
        self.body = body
        self.headers = headers


class InvalidArgument(ApiError):
    def __init__(self, message: str) -> None:
        super().__init__(
            status.HTTP_400_BAD_REQUEST,
            {"error": message, "type": "InvalidArgumentException"},
        )


async def api_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApiError)
    return JSONResponse(exc.body, status_code=exc.status_code, headers=exc.headers)
