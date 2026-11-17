"""Pydantic models.

Response bodies copy the shapes that https://api.siposm.hu returns, so a
frontend written against the original API works against this one unchanged.
"""

from typing import Annotated, Literal, Self
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    StringConstraints,
    computed_field,
    field_validator,
    model_validator,
)

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Salary = Annotated[int | float, Field(ge=0, examples=[650000])]
Age = Annotated[int, Field(ge=14, le=120, examples=[40])]


def new_id() -> str:
    return str(uuid4())


class ApiModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


# --- words -----------------------------------------------------------------


class WordCountRequest(ApiModel):
    # The original API takes the count as a string ("5"); lax mode accepts both.
    count: Annotated[int, Field(examples=["5"])]


class WordCountResponse(BaseModel):
    count: int
    words: list[str]


class InvalidArgumentResponse(BaseModel):
    error: str
    type: Literal["InvalidArgumentException"] = "InvalidArgumentException"


# --- developers ------------------------------------------------------------


def _clean_skills(skills: list[str]) -> list[str]:
    """Drop duplicates while keeping the order the client sent."""
    return list(dict.fromkeys(skills))


class Developer(ApiModel):
    """A stored developer record. Clients create the id; a missing id gets a UUID."""

    id: NonEmptyStr = Field(
        default_factory=new_id, examples=["12378c6c-eda2-35ee-f621-91f9b7af1asd"]
    )
    name: NonEmptyStr = Field(examples=["John Doe"])
    email: EmailStr = Field(examples=["john@doe.com"])
    job: NonEmptyStr = Field(examples=["Frontend Developer"])
    age: Age
    salary: Salary
    image: HttpUrl | None = Field(
        default=None, examples=["https://randomuser.me/api/portraits/men/1.jpg"]
    )
    skills: list[NonEmptyStr] = Field(default_factory=list, examples=[["HTML", "CSS"]])

    _dedupe_skills = field_validator("skills")(_clean_skills)


class DeveloperUpdate(ApiModel):
    """Body of PUT /updateDeveloper. Fields left out keep their stored value."""

    id: NonEmptyStr
    name: NonEmptyStr | None = None
    email: EmailStr | None = None
    job: NonEmptyStr | None = None
    age: Age | None = None
    salary: Salary | None = None
    image: HttpUrl | None = None
    skills: list[NonEmptyStr] | None = None

    @field_validator("skills")
    @classmethod
    def _dedupe(cls, v: list[str] | None) -> list[str] | None:
        return None if v is None else _clean_skills(v)

    @model_validator(mode="after")
    def _has_changes(self) -> Self:
        if self.model_fields_set <= {"id"}:
            raise ValueError("at least one field besides 'id' must be given")
        return self


class DeveloperMessage(BaseModel):
    status: Literal["success", "error"]
    message: str


# --- skills and jobs -------------------------------------------------------


class CatalogItemCreate(ApiModel):
    name: NonEmptyStr = Field(examples=["Frontend development"])
    description: str = Field(default="", examples=["Lorem ipsum dolor sit amet..."])


class CatalogItem(ApiModel):
    id: NonEmptyStr = Field(default_factory=new_id)
    name: NonEmptyStr = Field(examples=["Frontend development"])
    description: str = Field(default="", examples=["Lorem ipsum dolor sit amet..."])


class IdBody(ApiModel):
    id: NonEmptyStr


class StatusMessage(BaseModel):
    status: str


class SkillCreated(StatusMessage):
    skill: CatalogItem


class JobCreated(StatusMessage):
    job: CatalogItem


# --- auth ------------------------------------------------------------------


class LoginRequest(ApiModel):
    username: NonEmptyStr = Field(examples=["johndoe"])
    password: str = Field(min_length=1, examples=["johndoe123"])


class TokenResponse(BaseModel):
    token: str


class ErrorMessage(BaseModel):
    error: str


# --- status ----------------------------------------------------------------


class StatusMeta(BaseModel):
    api_version: str
    environment: str
    server_time: str
    request_id: str


class StatusHealth(BaseModel):
    database: bool
    cache: bool


class StatusPerformance(BaseModel):
    response_time_ms: float
    memory_usage: int
    memory_peak: int


class StatusDemo(BaseModel):
    random_token: str
    example: str = "This is a demo API response."


class StatusResponse(BaseModel):
    success: bool = True
    meta: StatusMeta
    health: StatusHealth
    performance: StatusPerformance
    demo: StatusDemo

    @computed_field
    @property
    def status(self) -> Literal["ok", "degraded"]:
        return "ok" if self.health.database and self.health.cache else "degraded"


class ResetResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    developers: int
    skills: int
    jobs: int
    words: int
