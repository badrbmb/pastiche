from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import extract

from pastiche import tables


def read_first_game(db: Session) -> tables.JumbleGame:
    return db.query(tables.JumbleGame).first()


def read_jumble_game(db: Session, value_date: datetime) -> tables.JumbleGame:
    return (
        db.query(tables.JumbleGame)
        .filter(
            extract("year", tables.JumbleGame.value_date) == value_date.year,
            extract("month", tables.JumbleGame.value_date) == value_date.month,
            extract("day", tables.JumbleGame.value_date) == value_date.day,
        )
        .first()
    )
