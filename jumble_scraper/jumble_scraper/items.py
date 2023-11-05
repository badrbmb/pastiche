from dataclasses import dataclass, asdict


@dataclass
class JumbleScraperItem:
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
