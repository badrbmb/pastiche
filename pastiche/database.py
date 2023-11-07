from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pastiche.game import JumbleGameCollection
from pastiche import tables
from pastiche.config import LOCAL_DB_PATH

DB_URL = f"sqlite:///{LOCAL_DB_PATH}"
engine = create_engine(DB_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables(drop_if_exists: True):
    """Helper to create all tables defined under pastiche.tables. If db exists, drop and recreate new ones"""
    if drop_if_exists:
        tables.Base.metadata.drop_all(engine)
    # create tables
    tables.Base.metadata.create_all(engine)


def populate_database(path: str | Path) -> None:
    """Populates database with historical jumble games"""

    historical_games = JumbleGameCollection.parse_historical_jumbles(path)

    with SessionLocal() as db:
        jumble_games = []
        for game in historical_games.games:
            game_dict = game.model_dump()
            jumbles_list = game_dict.pop("jumbles")
            jumbles = [tables.Jumble(**t) for t in jumbles_list]
            jumble_games.append(tables.JumbleGame(**game_dict, jumbles=jumbles))

        db.add_all(jumble_games)
        db.commit()


if __name__ == "__main__":
    # create_tables(drop_if_exists=True)
    # populate_database(path="./data/jumble_data.json")

    with SessionLocal() as db:
        result = db.query(tables.JumbleGame).first()
        print(result.jumbles[0].jumbled)
