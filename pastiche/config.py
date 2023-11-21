from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()

DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

LOCAL_DB_PATH = (DATA_DIR / "pastiche.db").as_posix()

LOCAL_GAMES_PATH = DATA_DIR / "jumble_answers_data.json"

STATIC_DIRECTORY = (ROOT_DIR / "static").as_posix()
TEMPLATES_DIRECTORY = (ROOT_DIR / "templates").as_posix()

DISPLAY_DATE_FORMAT = "%A, %B %d %Y"

SANITIZE_SUB = "*"

BASE_IMAGE_URL = "https://storage.googleapis.com/pastiche-images/thumbnails"

BUCKET_IMG = "pastiche-images"
