import re
import pandas as pd
from pydantic import BaseModel, Field, field_validator, computed_field, ValidationError
from datetime import datetime
from tqdm import tqdm

WORD_LIST = {"A", "AN", "FOR", "HER", "HIS", "IN", "IT", "THE", "THEIR", "TO", "WAS"}


class Jumble(BaseModel):
    jumbled: str = Field(..., description="Scrambled word")
    unjumbled: str = Field(..., description="The un-scrambled word")
    _clue_indices: list[int]

    @field_validator("unjumbled")
    def solution_has_same_letters_as_scrambled(cls, input_value: str, values):
        scrambled = values.data.get("jumbled")
        input_value = cls.clean_string(input_value)
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

    def clean_string(input_string):
        cleaned_string = re.sub(r"\*.*\*", "", input_string)
        return cleaned_string.strip()


class JumbleGame(BaseModel):
    url_from: str
    value_date: datetime | str
    solution_unjumbled: str = Field(
        ..., description="The unjumbled solution to the clue sentence"
    )
    solution_jumbled: str = Field(
        ..., description="The jumbled solution to the clue sentence"
    )
    jumbles: list[Jumble]
    clue_sentence: str = Field(
        ..., description="The sentence with missing words to guess"
    )

    @field_validator("value_date")
    def format_value_date(cls, value: str | datetime) -> datetime:
        if isinstance(value, str):
            value = datetime.strptime(value, "%Y-%m-%d")
        return value

    @field_validator("jumbles")
    def assign_clue_indices_to_each_jumble(
        cls, value: list[Jumble], values
    ) -> list[Jumble]:
        solution = cls.clean_string(values.data.get("solution_unjumbled"))
        jumbles = []
        for jumble, indices in cls.find_indices(solution, jumbles=value).items():
            if len(indices) > 0:
                # only add jumble word if it its contributing to the solution
                jumble.clue_indices = indices
                jumbles.append(jumble)

        # make sure the letter from all the jumbles return the desired word
        clue_letters = "".join(
            [cls.create_substring(t.unjumbled, t.clue_indices) for t in jumbles]
        )
        assert set(solution) == set(clue_letters), ValueError(
            "clue letters do not match the solution!"
        )
        return jumbles

    @staticmethod
    def add_parentheses(text: str, word_list: set[str]):
        """wraps any occurence of words in the word_list between parentheses"""
        for word in word_list:
            text = re.sub(r"\b" + word + r"\b", "(" + word + ")", text)
        return text

    @staticmethod
    def clean_string(value: str) -> str:
        cleaned_string = re.sub(r"[^a-zA-Z]", "", re.sub("\s*\(.*?\)\s*", "", value))
        return cleaned_string.upper()

    @computed_field
    @property
    def solution(self) -> str:
        return self.clean_string(self.solution_unjumbled)

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
                for i, w_letter in enumerate(jumble.unjumbled):
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

    @classmethod
    def from_row(cls, row: pd.Series) -> "JumbleGame":
        data = row.to_dict()
        data["jumbles"] = [Jumble(**t) for t in data["jumbles"]]
        try:
            return cls(**data)
        except ValidationError:
            # special cases where the jumbled solution needs extra cleaning
            data["solution_unjumbled"] = cls.add_parentheses(
                data["solution_unjumbled"], WORD_LIST
            )
            return cls(**data)


class JumbleGameCollection:
    def __init__(self, games: list[JumbleGame]) -> None:
        self.games = games

    @classmethod
    def from_jumble_answers(cls, path: str) -> "JumbleGameCollection":
        df = pd.read_json(path, lines=True)
        return JumbleGameCollection(
            games=[
                JumbleGame.from_row(row)
                for _, row in tqdm(df.iterrows(), total=len(df))
            ]
        )
