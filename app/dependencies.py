import random
import time
from dataclasses import dataclass, field
from typing import Annotated

from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings
from app.errors import ApiError
from app.store import Store


def get_store(request: Request) -> Store:
    return request.app.state.store


def get_rng() -> random.Random:
    """Source of randomness for word sampling. Tests override it with a seeded one."""
    return random.Random()


@dataclass
class TokenRegistry:
    """Issued bearer tokens and their expiry, as monotonic timestamps."""

    ttl_seconds: int
    _tokens: dict[str, float] = field(default_factory=dict)

    def add(self, token: str) -> None:
        self._tokens[token] = time.monotonic() + self.ttl_seconds

    def is_valid(self, token: str) -> bool:
        expires = self._tokens.get(token)
        if expires is None:
            return False
        if expires < time.monotonic():
            del self._tokens[token]
            return False
        return True

    def clear(self) -> None:
        self._tokens.clear()


def get_tokens(request: Request) -> TokenRegistry:
    return request.app.state.tokens


bearer = HTTPBearer(auto_error=False, description="Token returned by POST /login")


def require_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    tokens: Annotated[TokenRegistry, Depends(get_tokens)],
) -> str:
    challenge = {"WWW-Authenticate": "Bearer"}
    if credentials is None:
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED, {"status": "Authorization token required."}, challenge
        )
    if not tokens.is_valid(credentials.credentials):
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED, {"status": "Invalid or expired token."}, challenge
        )
    return credentials.credentials


SettingsDep = Annotated[Settings, Depends(get_settings)]
StoreDep = Annotated[Store, Depends(get_store)]
RngDep = Annotated[random.Random, Depends(get_rng)]
TokensDep = Annotated[TokenRegistry, Depends(get_tokens)]
