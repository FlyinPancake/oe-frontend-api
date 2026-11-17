"""In-memory data store, seeded from the JSON files in `data_dir`.

All endpoints that touch the store are `async def` and never await while
mutating, so every change runs to completion on the event loop without a lock.
"""

from pathlib import Path

from pydantic import TypeAdapter

from app.models import CatalogItem, Developer

_developers = TypeAdapter(list[Developer])
_catalog = TypeAdapter(list[CatalogItem])
_words = TypeAdapter(list[str])


class Store:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.developers: dict[str, Developer] = {}
        self.skills: dict[str, CatalogItem] = {}
        self.jobs: dict[str, CatalogItem] = {}
        self.words: list[str] = []
        self.reset()

    def _read(self, name: str) -> bytes:
        return (self.data_dir / f"{name}.json").read_bytes()

    def reset(self) -> None:
        """Restore every collection to the seed data."""
        self.developers = {d.id: d for d in _developers.validate_json(self._read("developers"))}
        self.skills = {s.id: s for s in _catalog.validate_json(self._read("skills"))}
        self.jobs = {j.id: j for j in _catalog.validate_json(self._read("jobs"))}
        self.words = _words.validate_json(self._read("words"))
