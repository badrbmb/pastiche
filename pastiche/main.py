from itertools import groupby
import pandas as pd
from datetime import date, datetime
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Form
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
    game = crud.read_jumble_game(db, value_date=value_date)
    if game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No game found for {value_date}",
        )
    context = {"request": request}
    context.update(**game.to_sanitized_dict())
    return templates.TemplateResponse("index.html", context)


@app.post("/check")
async def check_submission(
    value_date: str = Form(...),
    jumble_letters: list[str] = Form(...),
    solution_letters: list[str] = Form(...),
    db: Session = Depends(get_db),
):
    # convert back to date
    value_date = datetime.strptime(value_date, config.DISPLAY_DATE_FORMAT)
    # load jumble solution
    game = crud.read_jumble_game(db, value_date=value_date)
    # check if global solution is correct
    is_correct = "".join(solution_letters) == game.solution
    # check if each jumble is correct
    seen_letters = 0
    jumbles_correct = {}
    for i, jumble in enumerate(game.jumbles):
        n_jumble = len(jumble.unjumbled)
        to_check = jumble_letters[seen_letters : seen_letters + n_jumble]
        jumbles_correct[i + 1] = "".join(to_check) == jumble.unjumbled

        seen_letters += n_jumble

    return {"is_correct": is_correct, "is_jumbles_correct": jumbles_correct}


@app.post("/statistics")
async def compute_statistics(value_dates: list[dict[str, str | int]]):
    """End point to compute statistics based on a list of value_date played"""
    if len(value_dates) > 0:
        df = pd.DataFrame(value_dates)
        df["valueDate"] = df["valueDate"].apply(
            lambda x: datetime.strptime(x, config.DISPLAY_DATE_FORMAT)
        )
        fastest_time = int(df["elapsedTime"].min())
        count_played = int(df["valueDate"].nunique())

        df.set_index("valueDate", inplace=True)
        df = df.resample("D").first()
        df.sort_index(inplace=True)

        played_dates = ~df["elapsedTime"].isnull()

        consecutive_dates = []
        for k, g in groupby(enumerate(played_dates), lambda x: x[1]):
            if k:
                consecutive_dates.append(list(map(lambda x: x[0], list(g))))

        max_streak = int(max([len(t) for t in consecutive_dates]))
        current_streak = int([len(t) for t in consecutive_dates][-1])
    else:
        count_played = 0
        fastest_time = None
        max_streak = 0
        current_streak = 0

    return {
        "played": count_played,
        "fastest": fastest_time,
        "max_streak": max_streak,
        "current_streak": current_streak,
    }
