from datetime import date, datetime
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi import HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from pastiche.database import SessionLocal, check_and_populate_db
from pastiche import crud, config


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


@app.get("/play")
async def play_jumble():
    today = datetime.utcnow().date().strftime("%Y-%m-%d")
    return RedirectResponse(url=f"/{today}")


@app.get("/{value_date}")
async def load_daily_jumble(
    request: Request, value_date: date, db: Session = Depends(get_db)
):
    game = crud.read_jumble_game(db, value_date=value_date) or crud.read_first_game(db)
    if game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game for {value_date} not found!",
        )
    context = {"request": request}
    context.update(**game.to_sanitized_dict())
    return templates.TemplateResponse("index.html", context)
