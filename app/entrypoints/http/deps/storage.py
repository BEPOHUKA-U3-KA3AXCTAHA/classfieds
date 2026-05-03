from app.infra.config import get_settings
from app.modules.listings.ports.image_storage import ImageStorage
from app.modules.listings.adapters.local_image_storage import LocalImageStorage


_storage: LocalImageStorage | None = None


def image_storage() -> ImageStorage:
    global _storage
    if _storage is None:
        s = get_settings()
        _storage = LocalImageStorage(media_dir=s.media_dir, url_prefix=s.media_url_prefix)
    return _storage
