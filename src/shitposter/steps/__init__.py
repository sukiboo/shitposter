from shitposter.steps.base import Step
from shitposter.steps.choose_holiday import ChooseHolidayStep
from shitposter.steps.construct_header import ConstructHeaderStep
from shitposter.steps.generate_image import GenerateImageStep
from shitposter.steps.generate_text import GenerateCaptionStep, GenerateTextStep
from shitposter.steps.publish_post import PublishPostStep
from shitposter.steps.resolve_date import ResolveDateStep
from shitposter.steps.retrieve_holidays import RetrieveHolidaysStep

STEPS: dict[str, type[Step]] = {
    "choose_holiday": ChooseHolidayStep,
    "construct_header": ConstructHeaderStep,
    "resolve_date": ResolveDateStep,
    "retrieve_holidays": RetrieveHolidaysStep,
    "generate_text": GenerateTextStep,
    "generate_caption": GenerateCaptionStep,
    "generate_image": GenerateImageStep,
    "publish_post": PublishPostStep,
}
