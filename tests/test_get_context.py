from unittest.mock import patch

from shitposter.clients.web_to_context import CheckiDayProvider
from shitposter.steps.collect_context import CollectContextStep

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

EMPTY_HTML = "<html><body><p>Nothing here</p></body></html>"


def test_parse_holidays():
    holidays = CheckiDayProvider._parse(SAMPLE_HTML)
    assert len(holidays) == 2
    assert holidays[0]["name"] == "Be Electrific Day"
    assert holidays[0]["url"] == "https://www.checkiday.com/be-electrific-day"
    assert holidays[1]["url"] == "https://www.checkiday.com/guitar-day"
    assert holidays[0]["description"] == "A day to be electrifying!"
    assert holidays[1]["name"] == "Get Out Your Guitar Day"


def test_parse_empty():
    assert CheckiDayProvider._parse(EMPTY_HTML) == []


def test_format():
    holidays = [{"name": "Day A"}, {"name": "Day B"}]
    result = CollectContextStep._format(holidays)
    assert result == ["Day A", "Day B"]


def test_format_empty():
    assert CollectContextStep._format([]) == []


def test_step_sets_state(run_ctx):
    holidays = [{"name": "Test Day", "url": None, "description": "A test"}]

    with patch.object(CheckiDayProvider, "generate", return_value=holidays):
        result = CollectContextStep(run_ctx, {"provider": "checkiday"}, "context").execute()

    assert run_ctx.state["context"] == ["Test Day"]
    assert run_ctx.run_dir.joinpath("context.json").exists()
    assert result.metadata["count"] == 1
