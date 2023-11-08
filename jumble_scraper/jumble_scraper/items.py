from dataclasses import dataclass, asdict
from pydantic import BaseModel, computed_field
from urllib.parse import urlparse
from datetime import datetime


@dataclass
class JumbleSolverItem:
    url_from: str
    jumbled: str
    _unjumbled: str | None = None

    @property
    def unjumbled(self) -> str | None:
        return self._unjumbled

    @unjumbled.setter
    def unjumbled(self, value: str):
        self._unjumbled = value

    @property
    def value_date(self) -> str:
        return self.url_from.split("/")[-1]

    def to_dict(self, exclude_fields: set[str] | None) -> dict[str, str]:
        out = asdict(self)
        out.update({"unjumbled": self.unjumbled, "value_date": self.value_date})
        if exclude_fields:
            out = {u: v for u, v in out.items() if u not in exclude_fields}
        return out


class JumbleAnswerItem(BaseModel):
    jumbled: str
    unjumbled: str


class JumbleGameAnswerItem(BaseModel):
    url_from: str
    clue_sentence: str
    solution_jumbled: str
    solution_unjumbled: str
    jumbles: list[JumbleAnswerItem]

    class Config:
        arbitrary_types_allowed = True

    @computed_field
    @property
    def value_date(self) -> str:
        return self.extract_date_from_url(self.url_from)

    @staticmethod
    def extract_date_from_url(url):
        path = urlparse(url).path
        parts = path.strip("/").split("/")
        date_string = "/".join(parts[:3])
        return datetime.strptime(date_string, "%Y/%m/%d").strftime("%Y-%m-%d")
