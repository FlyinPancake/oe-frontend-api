import secrets

from fastapi import APIRouter, status

from app.dependencies import SettingsDep, TokensDep
from app.errors import ApiError
from app.models import ErrorMessage, LoginRequest, TokenResponse

router = APIRouter(tags=["auth"])


@router.post(
    "/login",
    responses={401: {"model": ErrorMessage, "description": "Wrong username or password"}},
    summary="Log in and get a bearer token",
)
async def login(body: LoginRequest, settings: SettingsDep, tokens: TokensDep) -> TokenResponse:
    # compare_digest on both fields so the response time does not reveal which one was wrong.
    user_ok = secrets.compare_digest(body.username.encode(), settings.demo_username.encode())
    pass_ok = secrets.compare_digest(
        body.password.encode(), settings.demo_password.get_secret_value().encode()
    )
    if not (user_ok and pass_ok):
        raise ApiError(status.HTTP_401_UNAUTHORIZED, {"error": "Invalid username or password."})
    token = secrets.token_hex(32)
    tokens.add(token)
    return TokenResponse(token=token)
