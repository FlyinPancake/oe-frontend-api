from typing import Annotated

from fastapi import APIRouter, Body, Query, status

from app.dependencies import StoreDep
from app.errors import ApiError
from app.models import Developer, DeveloperMessage, DeveloperUpdate, IdBody

router = APIRouter(tags=["developers"])

_not_found = {404: {"model": DeveloperMessage, "description": "No developer with this id"}}


def _not_found_error() -> ApiError:
    return ApiError(
        status.HTTP_404_NOT_FOUND, {"status": "error", "message": "Developer not found."}
    )


@router.get("/getDevelopers", summary="List developers")
async def get_developers(
    store: StoreDep,
    job: Annotated[str | None, Query(description="Only developers with this job title")] = None,
    skill: Annotated[str | None, Query(description="Only developers with this skill")] = None,
) -> list[Developer]:
    developers = list(store.developers.values())
    if job is not None:
        developers = [d for d in developers if d.job.casefold() == job.casefold()]
    if skill is not None:
        developers = [d for d in developers if skill.casefold() in map(str.casefold, d.skills)]
    return developers


@router.post(
    "/createDeveloper",
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": DeveloperMessage, "description": "The id is already taken"}},
    summary="Create a developer",
)
async def create_developer(developer: Developer, store: StoreDep) -> DeveloperMessage:
    if developer.id in store.developers:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            {"status": "error", "message": "Developer with this ID already exists."},
        )
    store.developers[developer.id] = developer
    return DeveloperMessage(
        status="success", message="Developer data received and saved successfully."
    )


@router.put("/updateDeveloper", responses=_not_found, summary="Update a developer")
async def update_developer(
    changes: Annotated[
        DeveloperUpdate,
        Body(
            openapi_examples={
                "raise": {
                    "value": {"id": "a49335ca-d76a-02d1-2a6c-fdab1a3f8c0a", "salary": 2575000}
                }
            }
        ),
    ],
    store: StoreDep,
) -> DeveloperMessage:
    current = store.developers.get(changes.id)
    if current is None:
        raise _not_found_error()
    merged = current.model_dump() | changes.model_dump(exclude_unset=True)
    # Validate the merged record so cross-field rules still hold after a partial update.
    store.developers[changes.id] = Developer.model_validate(merged)
    return DeveloperMessage(status="success", message="Developer data updated successfully.")


@router.delete("/deleteDeveloper", responses=_not_found, summary="Delete a developer")
async def delete_developer(body: IdBody, store: StoreDep) -> DeveloperMessage:
    if store.developers.pop(body.id, None) is None:
        raise _not_found_error()
    return DeveloperMessage(status="success", message="Developer data deleted successfully.")
