import os
import time
from datetime import date

import httpx
from bs4 import BeautifulSoup

from shitposter.providers.base import ContextProvider

HTTP_TIMEOUT = 30
MAX_RETRIES = 5
BACKOFF_BASE = 2


class CheckiDayProviderAPI(ContextProvider):
    name = "checkiday_api"
    API_URL = "https://api.apilayer.com/checkiday/events"

    def __init__(self, **kwargs):
        self.api_key = os.environ["CHECKIDAY_API_KEY"]

    def generate(self, target_date: date) -> list[dict]:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = httpx.get(
                    self.API_URL,
                    headers={"apikey": self.api_key},
                    timeout=HTTP_TIMEOUT,
                )
                resp.raise_for_status()
                data = resp.json()
                return [
                    {"name": e["name"], "url": e.get("url"), "description": None}
                    for e in data.get("events", [])
                ]
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                self._meta["errors"].append(f"attempt {attempt}: {type(e).__name__}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_BASE**attempt)
        raise


class CheckiDayProviderScrape(ContextProvider):
    name = "checkiday_scrape"

    def generate(self, target_date: date) -> list[dict]:
        url = f"https://www.checkiday.com/{target_date.strftime('%m/%d/%Y')}"
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = httpx.get(url, follow_redirects=True, timeout=HTTP_TIMEOUT)
                resp.raise_for_status()
                return self._parse(resp.text)
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                self._meta["errors"].append(f"attempt {attempt}: {type(e).__name__}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_BASE**attempt)
        raise

    @staticmethod
    def _parse(html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        grid = soup.find(id="magicGrid")
        if not grid:
            return []

        records = []
        for card in grid.find_all(class_="mdl-card"):
            title_el = card.select_one("h2.mdl-card__title-text > a")
            if not title_el:
                continue

            name = title_el.get_text(strip=True)
            href = title_el.get("href")
            url = href if isinstance(href, str) and href.startswith("http") else None

            desc_el = card.select_one(".mdl-card__supporting-text")
            description = desc_el.get_text(strip=True) if desc_el else None

            if name.lower() == "on this day in history":
                continue

            records.append({"name": name, "url": url, "description": description})

        return records


class CheckiDayProvider(ContextProvider):
    name = "checkiday"

    def __init__(self, **kwargs):
        self._api = CheckiDayProviderAPI(**kwargs)
        self._scrape = CheckiDayProviderScrape(**kwargs)
        self._delegate = self._api
        self._fallback_error: str | None = None

    def generate(self, target_date: date) -> list[dict]:
        try:
            result = self._api.generate(target_date)
            self._delegate = self._api
            return result
        except Exception as e:
            self._fallback_error = f"{type(e).__name__}: {e}"
            self._delegate = self._scrape
            return self._scrape.generate(target_date)

    def metadata(self) -> dict:
        meta: dict[str, object] = {"provider": self._delegate.name}
        if self._fallback_error:
            meta["fallback_error"] = self._fallback_error
        if self._delegate._meta.get("errors"):
            meta["errors"] = self._delegate._meta["errors"]
        return meta
