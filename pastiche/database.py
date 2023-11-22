from pathlib import Path
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, NoResultFound, ProgrammingError

from pastiche.game import JumbleGameCollection
from pastiche import tables
from pastiche.config import LOCAL_DB_PATH, RESET_DATE

DB_URL = f"sqlite:///{LOCAL_DB_PATH}"
engine = create_engine(DB_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_tables(drop_if_exists: True):
    """Helper to create all tables defined under pastiche.tables. If db exists, drop and recreate new ones"""
    if drop_if_exists:
        tables.Base.metadata.drop_all(engine)
    # create tables
    tables.Base.metadata.create_all(engine)


def populate_database(path: str | Path, reset_dates: bool = True) -> None:
    """Populates database with historical jumble games"""

    historical_games = JumbleGameCollection.from_jumble_answers(path)

    with SessionLocal() as db:
        jumble_games = []
        for i, game in enumerate(historical_games.games):
            game_dict = game.model_dump()
            jumbles_list = game_dict.pop("jumbles")
            jumbles = [tables.Jumble(**t) for t in jumbles_list]
            if reset_dates:
                game_dict["value_date"] = RESET_DATE + timedelta(days=i)
            jumble_game = tables.JumbleGame(**game_dict, jumbles=jumbles)
            jumble_games.append(jumble_game)

        db.add_all(jumble_games)
        db.commit()


def check_and_populate_db(path: str | Path) -> None:
    """Check if the database exists and is populated, if not, create tables and populate database"""
    try:
        # try to get the first record from the table
        with SessionLocal() as db:
            record = db.query(tables.JumbleGame).first()
            if record is None:
                raise NoResultFound
    except (NoResultFound, OperationalError, ProgrammingError):
        # if the table does not exist or is empty, create tables and populate database
        logger.info(
            "Database is not created or not populated. Creating tables and populating database..."
        )
        create_tables(drop_if_exists=True)
        populate_database(path)

    logger.info("Database is ready (＾◡＾)っ✂╰⋃╯")


if __name__ == "__main__":
    from pastiche.config import LOCAL_GAMES_PATH

    check_and_populate_db(LOCAL_GAMES_PATH)
