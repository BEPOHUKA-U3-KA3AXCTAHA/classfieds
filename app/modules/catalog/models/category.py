from dataclasses import dataclass


@dataclass
class Category:
    id: int | None
    parent_id: int | None
    slug: str
    name_me: str
    name_ru: str
    name_en: str
    icon: str | None = None
    position: int = 0

    def name(self, lang: str) -> str:
        return getattr(self, f"name_{lang}", self.name_me)


class CategoryNotFound(Exception):
    pass
