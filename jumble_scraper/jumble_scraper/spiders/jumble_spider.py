import json
import re
from datetime import datetime, timedelta, date
from typing import Any
import scrapy

from jumble_scraper.items import JumbleScraperItem

RAW_URL = "https://jumblesolver.com"
ANSWERS_ENDPOINT = "/daily-jumble-answers"
DATE_FORMAT = "%Y-%m-%d"


class JumbleSpiderSpider(scrapy.Spider):
    name: str = "jumble_spider"

    def __init__(
        self,
        end_date: str | date = date.today(),
        date_offset: int = 10,
        output_path: str = "../../../data/jumble_data.json",
        force_update: bool = False,
        *args,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)

        if isinstance(end_date, str):
            end_date = date.strptime(end_date, DATE_FORMAT)

        self.end_date = end_date
        self.date_offset = int(date_offset)
        if isinstance(force_update, str):
            force_update = eval(force_update)
        self.force_update = force_update

        self.raw_url = RAW_URL
        self.answer_endpoint = ANSWERS_ENDPOINT
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
                value_date.strftime(DATE_FORMAT) not in self.visited_dates
                or self.force_update
            ):
                value_dates.append(value_date)
        return value_dates

    def parse(self, response):
        pass

    def start_requests(self):
        for value_date in self.value_dates:
            url = f"{self.raw_url}{self.answer_endpoint}/{value_date.strftime(DATE_FORMAT)}"
            yield scrapy.Request(url, callback=self.parse_jumbles)

    def parse_jumble_solution(self, response):
        item: JumbleScraperItem = response.meta["item"]
        # the un-jambled word is the first button on the page
        button = response.css("button.word")[0]
        item.unjumbled = button.css("::text").extract()[0]
        data = item.to_dict(exclude_fields={"_unjumbled", "url_from"})
        self.save_to_json(data)

    def parse_jumbles(self, response):
        content = response.css(".col-sm-7")[0]
        buttons = content.css("button.word")

        for button in buttons:
            # get jumbled word
            jumbled = button.css("::text").extract()[0]

            # scrap the un-jumbled work from associated url
            match = re.search(r"location.href='(.*?)'", button.attrib["onclick"])
            jumbled_endpoint = match.group(1)
            jumbled_url = f"{self.raw_url}{jumbled_endpoint}"

            item = JumbleScraperItem(url_from=response.url, jumbled=jumbled)
            yield scrapy.Request(
                jumbled_url,
                callback=self.parse_jumble_solution,
                meta={"item": item},
                dont_filter=True,
            )

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
