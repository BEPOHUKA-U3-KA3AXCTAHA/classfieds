from pathlib import Path
from fastapi.templating import Jinja2Templates

from app.infra.config import get_settings
from app.infra.i18n import t


TEMPLATE_DIR = Path(__file__).parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
templates.env.globals["settings"] = get_settings()
templates.env.globals["t"] = t
