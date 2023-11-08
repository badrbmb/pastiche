import json
from datetime import datetime, timedelta, date
from typing import Any
import scrapy

from jumble_scraper.items import (
    JumbleGameAnswerItem,
    JumbleAnswerItem,
)


class JumbleAnswersSpider(scrapy.Spider):
    name: str = "jumble_answers_spider"

    def __init__(
        self,
        end_date: str | date = date.today(),
        raw_url: str = "https://jumbleanswer.com",
        answers_endpoint_prefix: str = "/jumble-answers-for",
        date_offset: int = 10,
        output_path: str = "../../../data/jumble_answers_data.json",
        force_update: bool = False,
        date_format: str = "%Y-%m-%d",
        *args,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)

        self.date_format = date_format
        if isinstance(end_date, str):
            end_date = date.strptime(end_date, self.date_format)

        self.end_date = end_date
        self.date_offset = int(date_offset)
        if isinstance(force_update, str):
            force_update = eval(force_update)
        self.force_update = force_update

        self.raw_url = raw_url
        self.answers_endpoint_prefix = answers_endpoint_prefix
        self.output_path = output_path
        self.visited_dates = self.load_value_dates_from_json()

        self.value_dates = self.get_value_dates()

        self.logger.info(
            f"Init. new spider with {len(self.value_dates)} dates to scrap (end_date={self.end_date} | force_update={self.force_update})"
        )

    def get_value_dates(self) -> list[datetime]:
        value_dates = []
        for i in range(self.date_offset):
            value_date = self.end_date - timedelta(days=i)
            if (
                value_date.strftime(self.date_format) not in self.visited_dates
                or self.force_update
            ):
                value_dates.append(value_date)
        return value_dates

    def parse(self, response):
        pass

    def start_requests(self):
        for value_date in self.value_dates:
            year = value_date.year
            month = value_date.month
            day = value_date.day
            date_str = f"{month}-{day}-{value_date.strftime('%y')}"
            url = f"{self.raw_url}/{year}/{str(month).zfill(2)}/{str(day).zfill(2)}/{self.answers_endpoint_prefix}-{date_str}"
            yield scrapy.Request(url, callback=self.parse_jumbles)

    def parse_jumbles(self, response):
        content = ["".join(t.css("::text").extract()) for t in response.css("p")]

        index_ref = content.index("CARTOON ANSWER:")
        jumbles_text = content[:index_ref]
        clue_sentence_text = content[index_ref + 1]
        solution_text = content[index_ref + 2]

        # parse jumbles
        jumbles = []
        for jumble_txt in jumbles_text:
            jumbled, unjumbled = [t.strip() for t in jumble_txt.split("=")]
            jumbles.append(
                JumbleAnswerItem(**{"jumbled": jumbled, "unjumbled": unjumbled})
            )

        # parse the solution
        jumbled_solution, unjumbled_solution = [
            t.strip() for t in solution_text.split("=")
        ]

        jumble_game = JumbleGameAnswerItem(
            url_from=response.url,
            clue_sentence=clue_sentence_text.strip(),
            solution_jumbled=jumbled_solution,
            solution_unjumbled=unjumbled_solution,
            jumbles=jumbles,
        )
        self.save_to_json(jumble_game.model_dump())

    def load_value_dates_from_json(self) -> list[str]:
        try:
            with open(self.output_path) as file:
                visited_dates = [json.loads(line)["value_date"] for line in file]
                return visited_dates
        except FileNotFoundError:
            return []

    def save_to_json(self, data) -> None:
        with open(self.output_path, "a") as file:
            json.dump(data, file)
            file.write("\n")
