from pathlib import Path
from fastapi.templating import Jinja2Templates

from app.infra.config import get_settings
from app.infra.i18n import t, time_ago


TEMPLATE_DIR = Path(__file__).parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
templates.env.globals["settings"] = get_settings()
templates.env.globals["t"] = t
templates.env.globals["time_ago"] = time_ago
