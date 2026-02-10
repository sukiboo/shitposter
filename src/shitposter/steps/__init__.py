from shitposter.steps.base import Step
from shitposter.steps.generate_caption import GenerateCaptionStep
from shitposter.steps.generate_image import GenerateImageStep
from shitposter.steps.publish_post import PublishPostStep
from shitposter.steps.set_prompt import SetPromptStep

STEPS: dict[str, type[Step]] = {
    "set_prompt": SetPromptStep,
    "generate_image": GenerateImageStep,
    "generate_caption": GenerateCaptionStep,
    "publish_post": PublishPostStep,
}
