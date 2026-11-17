from random import Random
from typing import Annotated

from fastapi import APIRouter, Body, Query

from app.dependencies import RngDep, StoreDep
from app.errors import InvalidArgument
from app.models import InvalidArgumentResponse, WordCountRequest, WordCountResponse

router = APIRouter(prefix="/word", tags=["words"])

_errors = {400: {"model": InvalidArgumentResponse, "description": "Count is negative or too large"}}


def _sample(words: list[str], count: int, rng: Random) -> list[str]:
    if count < 0:
        raise InvalidArgument("Count must be non-negative.")
    if count > len(words):
        raise InvalidArgument(
            "Requested number of elements (count) is larger than the size of the array."
        )
    return rng.sample(words, count)


@router.get("", response_model=list[str], responses=_errors, summary="List words")
async def list_words(
    store: StoreDep,
    rng: RngDep,
    count: Annotated[
        int | None,
        Query(description="Return this many random words. Leave out to get every word."),
    ] = None,
) -> list[str]:
    if count is None:
        return store.words
    return _sample(store.words, count, rng)


@router.post("", responses=_errors, summary="Get random words, count in the body")
async def post_words(
    body: Annotated[WordCountRequest, Body(openapi_examples={"five": {"value": {"count": "5"}}})],
    store: StoreDep,
    rng: RngDep,
) -> WordCountResponse:
    return WordCountResponse(count=body.count, words=_sample(store.words, body.count, rng))
