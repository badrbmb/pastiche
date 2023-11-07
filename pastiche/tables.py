from typing import Any
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base

from pastiche.config import DISPLAY_DATE_FORMAT

Base = declarative_base()


class Jumble(Base):
    __tablename__ = "jumbles"

    id: Mapped[int] = mapped_column(primary_key=True)
    jumbled: Mapped[str] = mapped_column(nullable=False)
    unjumbled: Mapped[str] = mapped_column(nullable=False)
    clue_indices: Mapped[str] = mapped_column(nullable=False)
    jumble_game_id: Mapped[int] = mapped_column(ForeignKey("jumble_games.id"))

    jumble_game: Mapped["JumbleGame"] = relationship(back_populates="jumbles")

    def __init__(
        self,
        jumbled: str,
        unjumbled: str,
        clue_indices: list[int],
        *args,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.jumbled = jumbled
        self.unjumbled = unjumbled
        self.clue_indices = ",".join(str(index) for index in clue_indices)

    def get_clue_indices(self):
        return [int(index) for index in self.clue_indices.split(",")]

    def to_sanitized_dict(self):
        return {"jumbled": self.jumbled, "clue_indices": self.get_clue_indices()}


class JumbleGame(Base):
    __tablename__ = "jumble_games"

    id: Mapped[int] = mapped_column(primary_key=True)
    value_date: Mapped[datetime] = mapped_column(nullable=True)
    solution: Mapped[str] = mapped_column(nullable=False)
    clue_sentence: Mapped[str] = mapped_column(nullable=False)

    jumbles: Mapped[list["Jumble"]] = relationship(
        back_populates="jumble_game", cascade="all, delete-orphan"
    )

    def to_sanitized_dict(self) -> dict[str, Any]:
        return {
            "value_date": self.value_date.strftime(DISPLAY_DATE_FORMAT),
            "solution_lenght": len(self.solution),
            "clue_sentence": self.clue_sentence,
            "jumbles": [t.to_sanitized_dict() for t in self.jumbles],
        }
