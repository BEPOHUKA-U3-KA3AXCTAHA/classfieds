"""Локальное файловое хранилище картинок.

Сохраняет в `MEDIA_DIR/<listing_slug>/<hash>.<ext>`. Возвращает URL
вида `MEDIA_URL_PREFIX/<listing_slug>/<hash>.<ext>` для отдачи браузеру
(StaticFiles в FastAPI app поднимает MEDIA_DIR на этом prefix'е).
"""
import hashlib
from pathlib import Path
from io import BytesIO

from PIL import Image, UnidentifiedImageError


# конвертим в WebP — меньше, быстрее. Из исходного формата (PNG/JPG) в один общий.
WEBP_QUALITY = 82
MAX_DIM = 1600  # ужимаем большую сторону, чтобы не хранить 24-мегапиксельные оригиналы


class LocalImageStorage:
    def __init__(self, media_dir: str | Path, url_prefix: str = "/media") -> None:
        self._root = Path(media_dir)
        self._root.mkdir(parents=True, exist_ok=True)
        self._url_prefix = url_prefix.rstrip("/")

    async def save(self, content: bytes, filename: str, listing_slug: str) -> str:
        # хеш контента — детерминированное имя, дедуп бесплатно
        h = hashlib.sha256(content).hexdigest()[:20]

        # пытаемся открыть как картинку и конвертировать в WebP
        try:
            with Image.open(BytesIO(content)) as img:
                img = img.convert("RGB")
                # ресайз больших
                if max(img.size) > MAX_DIM:
                    ratio = MAX_DIM / max(img.size)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                target_dir = self._root / listing_slug
                target_dir.mkdir(parents=True, exist_ok=True)
                target_path = target_dir / f"{h}.webp"
                img.save(target_path, "WEBP", quality=WEBP_QUALITY, method=4)
                return f"{self._url_prefix}/{listing_slug}/{h}.webp"
        except UnidentifiedImageError:
            # не картинка — кладём как есть, но без преобразования (на случай GIF/SVG)
            ext = Path(filename).suffix.lower() or ".bin"
            target_dir = self._root / listing_slug
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / f"{h}{ext}"
            target_path.write_bytes(content)
            return f"{self._url_prefix}/{listing_slug}/{h}{ext}"
