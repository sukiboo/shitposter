from abc import ABC, abstractmethod
from collections import defaultdict


class ProviderBase(ABC):
    @property
    def _meta(self) -> defaultdict[str, list]:
        if not hasattr(self, "_meta_store"):
            self._meta_store: defaultdict[str, list] = defaultdict(list)
        return self._meta_store

    def metadata(self) -> dict:
        return {k: v for k, v in self._meta.items() if v}


class ImageProvider(ProviderBase):
    @abstractmethod
    def generate(self, prompt: str) -> bytes: ...


class TextProvider(ProviderBase):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...


class ContextProvider(ProviderBase):
    @abstractmethod
    def generate(self) -> list[dict]: ...


class TextToIntProvider(ProviderBase):
    @abstractmethod
    def generate(self, prompt: str, entries: list[str]) -> int: ...


class PublishingProvider(ProviderBase):
    @abstractmethod
    def publish(self, image_path: str | None, caption: str | None) -> dict: ...
