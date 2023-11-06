import re
import pandas as pd
from pydantic import BaseModel, Field, field_validator, computed_field
from datetime import datetime

MAX_LENGHT_CLUE = 17


class Jumble(BaseModel):
    jumbled: str = Field(..., description="Scrambled word")
    unjumbled: str = Field(..., description="The un-scrambled word")
    _clue_indices: list[int]

    @field_validator("unjumbled")
    def solution_has_same_letters_as_scrambled(cls, input_value: str, values):
        scrambled = values.data.get("jumbled")
        if set(scrambled) != set(input_value):
            raise ValueError(
                "The unjumbled must contain the same letters as the jumbled word"
            )
        return input_value

    @property
    def lenght(self) -> int:
        return len(self.jumbled)

    @computed_field
    @property
    def clue_indices(self) -> list[int]:
        return self._clue_indices

    @clue_indices.setter
    def clue_indices(self, value: list[int]) -> None:
        self.validate_indices(value)
        self._clue_indices = value

    def validate_indices(self, value: list[int]):
        assert max(value) < self.lenght
        assert min(value) >= 0

    def __hash__(self) -> int:
        return hash(self.unjumbled)


class JumbleGame(BaseModel):
    value_date: datetime | str
    solution: str = Field(..., description="The missing words in the clue_sentence")
    jumbles: list[Jumble]
    clue_sentence: str = Field(
        ..., description="The sentence with missing words to guess"
    )

    @field_validator("value_date")
    def format_value_date(cls, value: str | datetime) -> datetime:
        if isinstance(value, str):
            value = datetime.strptime(value, "%Y-%m-%d")
        return value

    @field_validator("solution")
    def remove_all_non_alphabetical_letters(cls, value: str) -> str:
        cleaned_string = re.sub(r"[^a-zA-Z]", "", value)
        return cleaned_string.upper()

    @field_validator("jumbles")
    def assign_clue_indices_to_each_jumble(
        cls, value: list[Jumble], values
    ) -> list[Jumble]:
        solution = values.data.get("solution")
        jumbles = []
        for jumble, indices in cls.find_indices(solution, jumbles=value).items():
            if len(indices) > 0:
                # only add jumble word if it its contributing to the solution
                jumble.clue_indices = indices
                jumbles.append(jumble)

        # make sure the letter from all the jumbles return the desired word
        clue_letters = "".join(
            [cls.create_substring(t.jumbled, t.clue_indices) for t in jumbles]
        )
        assert set(solution) == set(clue_letters), ValueError(
            "clue letters do not match the solution!"
        )
        return jumbles

    @staticmethod
    def find_indices(solution: str, jumbles: list[Jumble]):
        # Convert the solution word to a list so we can manipulate it
        solution_letters = list(solution)

        # This will store the indices for each letter found
        letter_indices = {word: [] for word in jumbles}

        # This will keep track of used letters so we don't reuse them
        used_indices = {word: [] for word in jumbles}

        for s_letter in solution_letters:
            found = False
            for jumble in jumbles:
                scrambled = jumble.jumbled
                for i, w_letter in enumerate(scrambled):
                    if s_letter == w_letter and i not in used_indices[jumble]:
                        # If the letter in the solution word matches the letter in the word
                        # And it has not been used yet, add the index to the list
                        letter_indices[jumble].append(i)
                        used_indices[jumble].append(i)
                        found = True
                        break  # Break the inner loop and go to the next letter in the solution word
                if found:
                    break  # Break the outer loop since we've found our letter

            if not found:
                raise ValueError(
                    f"Letter {s_letter} not found in any word of the initial list."
                )

        return letter_indices

    def set_clue_indices(self) -> None:
        for jumble, indices in self.find_indices().items():
            jumble.clue_indices = indices

    @staticmethod
    def create_substring(string, indices):
        substring = ""
        for index in indices:
            substring += string[index]
        return substring


class JumbleGameCollection(BaseModel):
    games: list[JumbleGame]

    @classmethod
    def parse_historical_jumbles(path: str) -> "JumbleGameCollection":
        """Function to parse dowloaded Jumble games into respective jumble objects with their computed properties"""
        df = pd.read_json(path_or_buf=path, lines=True)
        df.sort_values("value_date", inplace=True)

        df_clues = df[df["jumbled"].apply(lambda x: len(x) > MAX_LENGHT_CLUE)].copy()
        df_jumbles = df[df["jumbled"].apply(lambda x: len(x) <= MAX_LENGHT_CLUE)].copy()

        all_games = []
        for value_date, df_j in df_jumbles.groupby("value_date"):
            df_ref_clues = df_clues.loc[df_clues["value_date"] == value_date].copy()
            for _, row in df_ref_clues.iterrows():
                clue_sentence = row["jumbled"]
                solution = row["unjumbled"]
                # get all jumbles
                df_candidates = df_j[
                    ~df_j["unjumbled"].isin(df_ref_clues["unjumbled"].unique())
                ].copy()
                jumbles = [
                    Jumble(**t)
                    for t in df_candidates[["jumbled", "unjumbled"]].to_dict("records")
                ]
                # create game
                game = JumbleGame(
                    value_date=value_date,
                    jumbles=jumbles,
                    clue_sentence=clue_sentence,
                    solution=solution,
                )
                all_games.append(game)

        return JumbleGameCollection(
            games=sorted(all_games, key=lambda x: (x.value_date, x.solution))
        )
