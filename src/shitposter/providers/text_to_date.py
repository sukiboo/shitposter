from datetime import date

from shitposter.providers.base import DateProvider as DateProviderBase


class DateProvider(DateProviderBase):
    name = "date"

    def __init__(self, **kwargs):
        val = kwargs.get("value")
        if val is None:
            self.date = None
        elif isinstance(val, date):
            self.date = val
        else:
            self.date = date.fromisoformat(str(val))

    def generate(self) -> date:
        return self.date or date.today()
