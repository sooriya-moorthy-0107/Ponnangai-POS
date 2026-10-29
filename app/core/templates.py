import os
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR if os.path.isdir(TEMPLATES_DIR) else "templates")

