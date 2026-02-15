from shitposter.steps.base import Step
from shitposter.steps.choose_holiday import ChooseHolidayStep
from shitposter.steps.construct_header import ConstructHeaderStep
from shitposter.steps.construct_prompt import ConstructPromptStep
from shitposter.steps.generate_caption import GenerateCaptionStep
from shitposter.steps.generate_image import GenerateImageStep
from shitposter.steps.publish_post import PublishPostStep
from shitposter.steps.scrape_holidays import ScrapeHolidaysStep

STEPS: dict[str, type[Step]] = {
    "choose_holiday": ChooseHolidayStep,
    "construct_header": ConstructHeaderStep,
    "scrape_holidays": ScrapeHolidaysStep,
    "construct_prompt": ConstructPromptStep,
    "generate_image": GenerateImageStep,
    "generate_caption": GenerateCaptionStep,
    "publish_post": PublishPostStep,
}
