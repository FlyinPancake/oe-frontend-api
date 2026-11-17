"""CRUD routers for skills and jobs.

Both collections hold `{id, name, description}` records and share the same
endpoints and messages, so one factory builds both routers.
"""

from fastapi import APIRouter, Depends, status

from app.dependencies import StoreDep, require_token
from app.errors import ApiError
from app.models import (
    CatalogItem,
    CatalogItemCreate,
    IdBody,
    JobCreated,
    SkillCreated,
    StatusMessage,
)
from app.store import Store


def build_catalog_router(
    *, path: str, label: str, attr: str, created_model: type[SkillCreated | JobCreated]
) -> APIRouter:
    router = APIRouter(prefix=path, tags=[f"{label.lower()}s"])
    not_found = {404: {"model": StatusMessage, "description": f"No {label.lower()} with this id"}}

    def items(store: Store) -> dict[str, CatalogItem]:
        return getattr(store, attr)

    def missing() -> ApiError:
        return ApiError(status.HTTP_404_NOT_FOUND, {"status": f"No {label.lower()} with such ID."})

    @router.get("", summary=f"List {label.lower()}s")
    async def list_items(store: StoreDep) -> list[CatalogItem]:
        return list(items(store).values())

    @router.get("/{item_id}", responses=not_found, summary=f"Get one {label.lower()}")
    async def get_item(item_id: str, store: StoreDep) -> CatalogItem:
        if (item := items(store).get(item_id)) is None:
            raise missing()
        return item

    @router.post(
        "",
        status_code=status.HTTP_201_CREATED,
        response_model=created_model,
        summary=f"Create a {label.lower()}",
    )
    async def create_item(body: CatalogItemCreate, store: StoreDep):
        item = CatalogItem(**body.model_dump())
        items(store)[item.id] = item
        return {"status": f"{label} created successfully.", attr.removesuffix("s"): item}

    @router.put("", responses=not_found, summary=f"Update a {label.lower()}")
    async def update_item(body: CatalogItem, store: StoreDep) -> StatusMessage:
        if body.id not in items(store):
            raise missing()
        items(store)[body.id] = body
        return StatusMessage(status=f"{label} updated successfully.")

    @router.delete(
        "",
        responses={
            **not_found,
            401: {"model": StatusMessage, "description": "Missing or bad token"},
        },
        dependencies=[Depends(require_token)],
        summary=f"Delete a {label.lower()} (needs a bearer token)",
    )
    async def delete_item(body: IdBody, store: StoreDep) -> StatusMessage:
        if items(store).pop(body.id, None) is None:
            raise missing()
        return StatusMessage(status=f"{label} deleted successfully.")

    return router


skills = build_catalog_router(
    path="/skill", label="Skill", attr="skills", created_model=SkillCreated
)
jobs = build_catalog_router(path="/job", label="Job", attr="jobs", created_model=JobCreated)
