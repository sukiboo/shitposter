from datetime import date
from unittest.mock import patch

from shitposter.providers.web_to_context import (
    CheckiDayProvider,
    CheckiDayProviderAPI,
    CheckiDayProviderScrape,
)
from shitposter.steps.retrieve_holidays import RetrieveHolidaysStep

SAMPLE_API_RESPONSE = {
    "events": [
        {"name": "Be Electrific Day", "url": "https://www.checkiday.com/be-electrific-day"},
        {"name": "Get Out Your Guitar Day", "url": "https://www.checkiday.com/guitar-day"},
    ]
}

SAMPLE_HTML = """
<html><body>
<section id="magicGrid">
  <div class="mdl-card">
    <h2 class="mdl-card__title-text">
      <a href="https://www.checkiday.com/be-electrific-day">Be Electrific Day</a>
    </h2>
    <div class="mdl-card__supporting-text">A day to be electrifying!</div>
  </div>
  <div class="mdl-card">
    <h2 class="mdl-card__title-text">
      <a href="https://www.checkiday.com/guitar-day">Get Out Your Guitar Day</a>
    </h2>
    <div class="mdl-card__supporting-text">Strum away.</div>
  </div>
</section>
</body></html>
"""


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
@patch("httpx.get")
def test_api_generate_holidays(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.raise_for_status = lambda: None
    mock_get.return_value.json.return_value = SAMPLE_API_RESPONSE

    provider = CheckiDayProviderAPI()
    holidays = provider.generate(date(2026, 2, 11))

    assert len(holidays) == 2
    assert holidays[0]["name"] == "Be Electrific Day"
    assert holidays[0]["url"] == "https://www.checkiday.com/be-electrific-day"
    assert holidays[0]["description"] is None
    assert holidays[1]["name"] == "Get Out Your Guitar Day"

    mock_get.assert_called_once()
    call_kwargs = mock_get.call_args
    assert "params" not in call_kwargs.kwargs
    assert call_kwargs.kwargs["headers"] == {"apikey": "test-key"}


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
@patch("httpx.get")
def test_api_generate_empty(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.raise_for_status = lambda: None
    mock_get.return_value.json.return_value = {"events": []}

    provider = CheckiDayProviderAPI()
    assert provider.generate(date(2026, 1, 1)) == []


def test_scrape_parse_holidays():
    holidays = CheckiDayProviderScrape._parse(SAMPLE_HTML)
    assert len(holidays) == 2
    assert holidays[0]["name"] == "Be Electrific Day"
    assert holidays[0]["url"] == "https://www.checkiday.com/be-electrific-day"
    assert holidays[0]["description"] == "A day to be electrifying!"
    assert holidays[1]["name"] == "Get Out Your Guitar Day"


def test_scrape_parse_empty():
    assert CheckiDayProviderScrape._parse("<html><body><p>Nothing</p></body></html>") == []


def test_format():
    holidays = [{"name": "Day A"}, {"name": "Day B"}]
    result = RetrieveHolidaysStep._format(holidays)
    assert result == ["Day A", "Day B"]


def test_format_empty():
    assert RetrieveHolidaysStep._format([]) == []


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
def test_step_sets_state(run_ctx):
    holidays = [{"name": "Test Day", "url": None, "description": None}]
    run_ctx.state["date"] = date.today()

    with patch.object(CheckiDayProviderAPI, "generate", side_effect=lambda target_date: holidays):
        config = {"provider": "checkiday", "inputs": ["date"]}
        result = RetrieveHolidaysStep(run_ctx, config, "context", 0).execute()

    assert run_ctx.state["context"] == ["Test Day"]
    assert run_ctx.run_dir.joinpath("0_context.json").exists()
    assert result.metadata["params"]["provider"] == "checkiday_api"


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
def test_wrapper_uses_api_when_available():
    records = [{"name": "Test Day", "url": "https://example.com", "description": None}]
    provider = CheckiDayProvider()
    with (
        patch.object(CheckiDayProviderAPI, "generate", return_value=records) as mock_api,
        patch.object(CheckiDayProviderScrape, "generate") as mock_scrape,
    ):
        result = provider.generate(date.today())
    mock_api.assert_called_once()
    mock_scrape.assert_not_called()
    assert result == records
    assert provider.metadata()["provider"] == "checkiday_api"
    assert "fallback_error" not in provider.metadata()


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
def test_wrapper_falls_back_to_scrape_on_api_error():
    records = [{"name": "Fallback Day", "url": None, "description": "scraped"}]
    provider = CheckiDayProvider()
    with (
        patch.object(CheckiDayProviderAPI, "generate", side_effect=RuntimeError("API down")),
        patch.object(CheckiDayProviderScrape, "generate", return_value=records) as mock_scrape,
    ):
        result = provider.generate(date(2026, 2, 14))
    mock_scrape.assert_called_once_with(date(2026, 2, 14))
    assert result == records
    assert provider.metadata()["provider"] == "checkiday_scrape"
    assert "API down" in provider.metadata()["fallback_error"]


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
def test_wrapper_records_error_type_in_metadata():
    provider = CheckiDayProvider()
    with (
        patch.object(CheckiDayProviderAPI, "generate", side_effect=ConnectionError("timeout")),
        patch.object(CheckiDayProviderScrape, "generate", return_value=[]),
    ):
        provider.generate(date.today())
    assert provider.metadata()["fallback_error"] == "ConnectionError: timeout"


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
def test_wrapper_metadata_before_generate():
    provider = CheckiDayProvider()
    assert provider.metadata()["provider"] == "checkiday_api"
    assert "fallback_error" not in provider.metadata()
