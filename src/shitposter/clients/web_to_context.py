from datetime import date

import httpx
from bs4 import BeautifulSoup

from shitposter.clients.base import ContextProvider


class CheckiDayProvider(ContextProvider):
    def __init__(self, **kwargs):
        date_val = kwargs.get("date")
        if date_val is None:
            self._date = date.today()
        elif isinstance(date_val, date):
            self._date = date_val
        else:
            self._date = date.fromisoformat(str(date_val))

    def metadata(self) -> dict:
        return {"date": self._date.isoformat(), **super().metadata()}

    def generate(self) -> list[dict]:
        url = f"https://www.checkiday.com/{self._date.strftime('%m/%d/%Y')}"
        resp = httpx.get(url, follow_redirects=True, timeout=15)
        resp.raise_for_status()
        return self._parse(resp.text)

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
            url = href if href and href.startswith("http") else None

            desc_el = card.select_one(".mdl-card__supporting-text")
            description = desc_el.get_text(strip=True) if desc_el else None

            if name.lower() == "on this day in history":
                continue

            records.append({"name": name, "url": url, "description": description})

        return records


CONTEXT_PROVIDERS: dict[str, type[ContextProvider]] = {
    "checkiday": CheckiDayProvider,
}
