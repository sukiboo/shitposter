from shitposter.steps.base import Step
from shitposter.steps.choose_holiday import ChooseHolidayStep
from shitposter.steps.generate_image import GenerateImageStep
from shitposter.steps.generate_text import GenerateCaptionStep, GenerateTextStep
from shitposter.steps.publish_post import PublishPostStep
from shitposter.steps.resolve_date import ResolveDateStep
from shitposter.steps.retrieve_holidays import RetrieveHolidaysStep
from shitposter.steps.select_emojis import SelectEmojisStep

STEPS: dict[str, type[Step]] = {
    "choose_holiday": ChooseHolidayStep,
    "select_emojis": SelectEmojisStep,
    "resolve_date": ResolveDateStep,
    "retrieve_holidays": RetrieveHolidaysStep,
    "generate_text": GenerateTextStep,
    "generate_caption": GenerateCaptionStep,
    "generate_image": GenerateImageStep,
    "publish_post": PublishPostStep,
}
