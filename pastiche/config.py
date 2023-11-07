from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

LOCAL_DB_PATH = (DATA_DIR / "pastiche.db").as_posix()
