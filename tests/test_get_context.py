from collections import defaultdict
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest

from shitposter.providers.web_to_context import (
    API_DATE_FORMAT,
    MAX_RETRIES,
    CheckiDayProvider,
    CheckiDayProviderAPI,
    CheckiDayProviderScrape,
    _parse_description,
    _scrape_descriptions,
)
from shitposter.steps.retrieve_holidays import RetrieveHolidaysStep

SCRAPE_DESCRIPTIONS = "shitposter.providers.web_to_context._scrape_descriptions"

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

WRITE_UP_HTML = """
<html><head>
<script type="application/ld+json">
{"@type": "BreadcrumbList", "itemListElement": []}
</script>
<script type="application/ld+json">
{"@type": "Article", "headline": "Be Electrific Day",
 "description": "A day to be electrifying!\\nThomas Edison was born on this day."}
</script>
</head><body>
<p>A day to be electrifying!</p>
<h2>How to Observe Be Electrific Day</h2>
<p>Plug something in.</p>
</body></html>
"""

BLURB_HTML = """
<html><head>
<script type="application/ld+json">
{"@type": "Article", "headline": "Guitar Day",
 "description": "Guitar Day is being observed today! It has been observed since 2016."}
</script>
</head><body>
<p>Guitar Day is being observed today! It has been observed since 2016.</p>
<h2>Sponsor</h2>
</body></html>
"""


def _pass_through(records, meta):
    return records


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
@patch(SCRAPE_DESCRIPTIONS, side_effect=_pass_through)
@patch("httpx.get")
def test_api_generate_holidays(mock_get, mock_descriptions):
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
    assert call_kwargs.kwargs["params"] == {"date": "2026-02-11"}
    assert call_kwargs.kwargs["headers"] == {"apikey": "test-key"}


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
@patch("httpx.get")
def test_api_generate_empty(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.raise_for_status = lambda: None
    mock_get.return_value.json.return_value = {"events": []}

    provider = CheckiDayProviderAPI()
    assert provider.generate(date(2026, 1, 1)) == []


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
@patch(SCRAPE_DESCRIPTIONS, side_effect=_pass_through)
@patch("httpx.get")
def test_api_omits_date_for_today(mock_get, mock_descriptions):
    today = date.today()
    mock_get.return_value.raise_for_status = lambda: None
    mock_get.return_value.json.return_value = {
        **SAMPLE_API_RESPONSE,
        "date": today.strftime(API_DATE_FORMAT),
    }

    holidays = CheckiDayProviderAPI().generate(today)

    assert len(holidays) == 2
    assert mock_get.call_args.kwargs["params"] == {}


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
@patch("httpx.get")
def test_api_rejects_another_day_when_date_is_omitted(mock_get):
    today = date.today()
    yesterday = (today - timedelta(days=1)).strftime(API_DATE_FORMAT)
    mock_get.return_value.raise_for_status = lambda: None
    mock_get.return_value.json.return_value = {**SAMPLE_API_RESPONSE, "date": yesterday}

    with pytest.raises(ValueError, match=f"returned events for {yesterday}"):
        CheckiDayProviderAPI().generate(today)
    mock_get.assert_called_once()


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
@patch("time.sleep")
@patch("httpx.get")
def test_api_does_not_retry_forbidden(mock_get, mock_sleep):
    request = httpx.Request("GET", CheckiDayProviderAPI.API_URL)
    error = httpx.HTTPStatusError(
        "403 Forbidden", request=request, response=httpx.Response(403, request=request)
    )
    mock_get.return_value.raise_for_status.side_effect = error

    provider = CheckiDayProviderAPI()
    with pytest.raises(httpx.HTTPStatusError):
        provider.generate(date(2026, 2, 11))

    mock_get.assert_called_once()
    mock_sleep.assert_not_called()
    assert len(provider.metadata()["errors"]) == 1


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
@patch("time.sleep")
@patch("httpx.get")
def test_api_retries_server_errors(mock_get, mock_sleep):
    request = httpx.Request("GET", CheckiDayProviderAPI.API_URL)
    error = httpx.HTTPStatusError(
        "500 Server Error", request=request, response=httpx.Response(500, request=request)
    )
    mock_get.return_value.raise_for_status.side_effect = error

    with pytest.raises(httpx.HTTPStatusError):
        CheckiDayProviderAPI().generate(date(2026, 2, 11))

    assert mock_get.call_count == MAX_RETRIES
    assert mock_sleep.call_count == MAX_RETRIES - 1


def test_parse_description_returns_first_paragraph():
    assert _parse_description(WRITE_UP_HTML) == "A day to be electrifying!"


def test_parse_description_ignores_generated_blurb():
    assert _parse_description(BLURB_HTML) is None


def test_parse_description_without_article_metadata():
    html = "<html><body><h2>How to Observe Guitar Day</h2></body></html>"
    assert _parse_description(html) is None


@patch("httpx.Client")
@patch("httpx.get")
def test_scrape_generate_keeps_only_holidays_with_write_up(mock_get, mock_client):
    pages = {
        "https://www.checkiday.com/be-electrific-day": WRITE_UP_HTML,
        "https://www.checkiday.com/guitar-day": BLURB_HTML,
    }
    mock_get.return_value.raise_for_status = lambda: None
    mock_get.return_value.text = SAMPLE_HTML
    client = mock_client.return_value.__enter__.return_value
    client.get.side_effect = lambda url: SimpleNamespace(
        text=pages[url], raise_for_status=lambda: None
    )

    provider = CheckiDayProviderScrape()
    holidays = provider.generate(date(2026, 2, 11))

    assert mock_get.call_args.args == ("https://www.checkiday.com/02/11/2026",)
    assert provider.metadata()["dropped"] == ["Get Out Your Guitar Day"]
    assert holidays == [
        {
            "name": "Be Electrific Day",
            "url": "https://www.checkiday.com/be-electrific-day",
            "description": "A day to be electrifying!",
        }
    ]


@patch("httpx.Client")
def test_scrape_descriptions_drops_holidays_without_write_up(mock_client):
    pages = {"https://example.com/a": WRITE_UP_HTML, "https://example.com/b": BLURB_HTML}
    client = mock_client.return_value.__enter__.return_value
    client.get.side_effect = lambda url: SimpleNamespace(
        text=pages[url], raise_for_status=lambda: None
    )
    records = [
        {"name": "Be Electrific Day", "url": "https://example.com/a", "description": None},
        {"name": "Guitar Day", "url": "https://example.com/b", "description": None},
        {"name": "No Link Day", "url": None, "description": None},
    ]
    meta: defaultdict[str, list] = defaultdict(list)

    result = _scrape_descriptions(records, meta)

    assert result == [
        {
            "name": "Be Electrific Day",
            "url": "https://example.com/a",
            "description": "A day to be electrifying!",
        }
    ]
    assert client.get.call_count == 2
    assert dict(meta) == {"dropped": ["Guitar Day", "No Link Day"]}


@patch("httpx.Client")
def test_scrape_descriptions_records_fetch_error(mock_client):
    client = mock_client.return_value.__enter__.return_value
    client.get.side_effect = httpx.ReadTimeout("slow")
    records = [{"name": "Slow Day", "url": "https://example.com/a", "description": None}]
    meta: defaultdict[str, list] = defaultdict(list)

    result = _scrape_descriptions(records, meta)

    assert result == []
    assert dict(meta) == {
        "errors": ["description of 'Slow Day': ReadTimeout: slow"],
        "dropped": ["Slow Day"],
    }


def test_scrape_parse_holidays():
    holidays = CheckiDayProviderScrape._parse(SAMPLE_HTML)
    assert len(holidays) == 2
    assert holidays[0]["name"] == "Be Electrific Day"
    assert holidays[0]["url"] == "https://www.checkiday.com/be-electrific-day"
    assert holidays[0]["description"] is None
    assert holidays[1]["name"] == "Get Out Your Guitar Day"


def test_scrape_parse_empty():
    assert CheckiDayProviderScrape._parse("<html><body><p>Nothing</p></body></html>") == []


def test_format():
    holidays = [
        {"name": "Day A", "description": "About A."},
        {"name": "Day B", "description": "About B."},
    ]
    result = RetrieveHolidaysStep._format(holidays)
    assert result == {"Day A": "About A.", "Day B": "About B."}


def test_format_empty():
    assert RetrieveHolidaysStep._format([]) == {}


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
def test_step_sets_state(run_ctx):
    holidays = [{"name": "Test Day", "url": None, "description": "About Test Day."}]
    run_ctx.state["date"] = date.today()

    with patch.object(CheckiDayProviderAPI, "generate", side_effect=lambda target_date: holidays):
        config = {"provider": "checkiday", "inputs": ["date"]}
        result = RetrieveHolidaysStep(run_ctx, config, "context", 0).execute()

    assert run_ctx.state["context"] == {"Test Day": "About Test Day."}
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


@patch.dict("os.environ", {"CHECKIDAY_API_KEY": "test-key"})
def test_wrapper_reports_dropped_holidays():
    provider = CheckiDayProvider()
    provider._api._meta["dropped"].append("Guitar Day")
    assert provider.metadata()["dropped"] == ["Guitar Day"]
