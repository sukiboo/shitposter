from shitposter.providers.web_to_context import ContextProvider
from shitposter.steps.base import Step, StepResult


class ScrapeHolidaysStep(Step):
    registry = ContextProvider._registry

    def execute(self) -> StepResult:
        records = self.provider.generate(self.inputs["date"])
        entries = self._format(records)
        self.output = entries

        artifact = {**self.metadata, "records": records}
        self.write_artifact(artifact)

        return StepResult(metadata=self.metadata, summary=f"scraped {len(entries)} holidays")

    @staticmethod
    def _format(records: list[dict]) -> list[str | None]:
        return [record["name"] for record in records]
