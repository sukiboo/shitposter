from shitposter.steps.base import Step
from shitposter.steps.collect_context import CollectContextStep
from shitposter.steps.construct_prompt import ConstructPromptStep
from shitposter.steps.generate_caption import GenerateCaptionStep
from shitposter.steps.generate_image import GenerateImageStep
from shitposter.steps.publish_post import PublishPostStep

STEPS: dict[str, type[Step]] = {
    "collect_context": CollectContextStep,
    "construct_prompt": ConstructPromptStep,
    "generate_image": GenerateImageStep,
    "generate_caption": GenerateCaptionStep,
    "publish_post": PublishPostStep,
}
