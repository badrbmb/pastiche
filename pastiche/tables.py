from typing import Any
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base

from pastiche.config import DISPLAY_DATE_FORMAT, SANITIZE_SUB

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
    url_from: Mapped[str] = mapped_column(nullable=False)
    value_date: Mapped[datetime] = mapped_column(nullable=True)
    solution: Mapped[str] = mapped_column(nullable=False)
    solution_unjumbled: Mapped[str] = mapped_column(nullable=False)
    solution_jumbled: Mapped[str] = mapped_column(nullable=False)
    clue_sentence: Mapped[str] = mapped_column(nullable=False)

    jumbles: Mapped[list["Jumble"]] = relationship(
        back_populates="jumble_game", cascade="all, delete-orphan"
    )

    @staticmethod
    def sanitize_solution(solution: str, letters: str, sub: str = SANITIZE_SUB):
        """
        Sanitises a solution by replacing all letters present in solution by _ without touching the words special characters or worlds between ()
        example:
        sanitize_solution('DAY IN (AND) DAY OUT', 'DAYINDAYOUT')
        >>> '*** ** (AND) *** ***'
        """
        output = []
        in_parenthesis = False
        for character in solution:
            # Check if character is '(', and then we start skipping
            if character == "(":
                in_parenthesis = True
            # Check if character is ')', and then we stop skipping
            elif character == ")":
                in_parenthesis = False
            # If character is not in parenthesis & found in letters, replace it with sub
            if (
                not in_parenthesis
                and character.upper() in letters.upper()
                and character.isalpha()
            ):
                output.append(sub)
            else:  # Append the character as it is.
                output.append(character)
        return "".join(output)

    @property
    def sanitized_solution(self):
        return self.sanitize_solution(self.solution_unjumbled, self.solution)

    def to_sanitized_dict(self) -> dict[str, Any]:
        return {
            "value_date": self.value_date.strftime(DISPLAY_DATE_FORMAT),
            "sanitized_solution": self.sanitized_solution,
            "clue_sentence": self.clue_sentence,
            "jumbles": [t.to_sanitized_dict() for t in self.jumbles],
        }
