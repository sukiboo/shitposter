import json
import os
import time
from collections import defaultdict
from datetime import date

import httpx
from bs4 import BeautifulSoup

from shitposter.providers.base import ContextProvider

HTTP_TIMEOUT = 30
MAX_RETRIES = 5
BACKOFF_BASE = 2
NON_RETRYABLE_STATUSES = {401, 403}  # Auth and plan errors do not succeed on retry
API_DATE_FORMAT = "%m/%d/%Y"
WRITE_UP_HEADING = "How to Observe"  # Only holidays with a write-up have this section


def _parse_description(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    headings = (h.get_text(strip=True) for h in soup.find_all("h2"))
    if not any(heading.startswith(WRITE_UP_HEADING) for heading in headings):
        return None
    for script in soup.find_all("script", type="application/ld+json"):
        data = json.loads(script.get_text())
        if data.get("@type") == "Article":
            return data["description"].split("\n")[0]
    return None


def _scrape_descriptions(records: list[dict], meta: defaultdict[str, list]) -> list[dict]:
    with httpx.Client(follow_redirects=True, timeout=HTTP_TIMEOUT) as client:
        for record in records:
            if not record["url"]:
                continue
            try:
                resp = client.get(record["url"])
                resp.raise_for_status()
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                meta["errors"].append(f"description of '{record['name']}': {type(e).__name__}: {e}")
                continue
            record["description"] = _parse_description(resp.text)
    meta["dropped"].extend(record["name"] for record in records if not record["description"])
    return [record for record in records if record["description"]]


class CheckiDayProviderAPI(ContextProvider):
    name = "checkiday_api"
    API_URL = "https://api.apilayer.com/checkiday/events"

    def __init__(self, **kwargs):
        self.api_key = os.environ["CHECKIDAY_API_KEY"]

    def generate(self, target_date: date) -> list[dict]:
        # Free plan rejects the date parameter; the API then answers for "today"
        params = {} if target_date == date.today() else {"date": target_date.isoformat()}
        last_exc: Exception = RuntimeError("no retries attempted")
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = httpx.get(
                    self.API_URL,
                    headers={"apikey": self.api_key},
                    params=params,
                    timeout=HTTP_TIMEOUT,
                )
                resp.raise_for_status()
                data = resp.json()
                expected_date = target_date.strftime(API_DATE_FORMAT)
                if not params and data["date"] != expected_date:
                    raise ValueError(
                        f"Checkiday API returned events for {data['date']}, "
                        f"expected {expected_date}"
                    )
                records = [
                    {"name": e["name"], "url": e.get("url"), "description": None}
                    for e in data.get("events", [])
                ]
                return _scrape_descriptions(records, self._meta)
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                last_exc = e
                self._meta["errors"].append(f"attempt {attempt}: {type(e).__name__}: {e}")
                if (
                    isinstance(e, httpx.HTTPStatusError)
                    and e.response.status_code in NON_RETRYABLE_STATUSES
                ):
                    break
                if attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_BASE**attempt)
        raise last_exc


class CheckiDayProviderScrape(ContextProvider):
    name = "checkiday_scrape"

    def generate(self, target_date: date) -> list[dict]:
        last_exc: Exception = RuntimeError("no retries attempted")
        url = f"https://www.checkiday.com/{target_date.strftime('%m/%d/%Y')}"
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = httpx.get(url, follow_redirects=True, timeout=HTTP_TIMEOUT)
                resp.raise_for_status()
                return _scrape_descriptions(self._parse(resp.text), self._meta)
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                last_exc = e
                self._meta["errors"].append(f"attempt {attempt}: {type(e).__name__}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_BASE**attempt)
        raise last_exc

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

            if name.lower() == "on this day in history":
                continue

            records.append({"name": name, "url": url, "description": None})

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
        for key in ("errors", "dropped"):
            if self._delegate._meta.get(key):
                meta[key] = self._delegate._meta[key]
        return meta
