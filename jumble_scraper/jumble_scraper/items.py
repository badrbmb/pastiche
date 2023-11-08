from pydantic import BaseModel, computed_field
from urllib.parse import urlparse
from datetime import datetime


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
