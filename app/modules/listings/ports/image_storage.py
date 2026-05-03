from typing import Protocol


class ImageStorage(Protocol):
    """Driven port: куда сохраняем загруженные картинки.

    Адаптеры: LocalImageStorage (диск), S3ImageStorage (когда деплоим).
    """

    async def save(self, content: bytes, filename: str, listing_slug: str) -> str:
        """Сохраняет байты файла, возвращает публичный URL для отдачи браузеру."""
        ...
