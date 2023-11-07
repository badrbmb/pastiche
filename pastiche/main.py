from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from fastapi.staticfiles import StaticFiles

from pastiche import tables
from pastiche.database import SessionLocal, check_and_populate_db
from pastiche import config


@asynccontextmanager
async def load_db(app: FastAPI):
    # make sure db is populated
    check_and_populate_db(config.LOCAL_GAMES_PATH),
    yield


tags = [
    {"name": "Pastiche", "description": "Re-creation of the Jumble Daily game"},
]

app = FastAPI(title="Pastiche", openapi_tags=tags, lifespan=load_db)

app.mount("/static", StaticFiles(directory=config.STATIC_DIRECTORY), name="static")

templates = Jinja2Templates(directory=config.TEMPLATES_DIRECTORY)


def get_db():
    """Helper function which opens a connection to the database and also manages closing the connection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
