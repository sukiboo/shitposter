from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import date
from typing import ClassVar


class ProviderBase(ABC):
    name: ClassVar[str]

    @property
    def _meta(self) -> defaultdict[str, list]:
        if not hasattr(self, "_meta_store"):
            self._meta_store: defaultdict[str, list] = defaultdict(list)
        return self._meta_store

    def metadata(self) -> dict:
        return {"provider": self.name, **{k: v for k, v in self._meta.items() if v}}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if "name" in cls.__dict__:
            for base in cls.__mro__[1:]:
                if base is not ProviderBase and "_registry" in base.__dict__:
                    base._registry[cls.__dict__["name"]] = cls
                    break


class ImageProvider(ProviderBase):
    _registry: ClassVar[dict[str, type["ImageProvider"]]] = {}

    @abstractmethod
    def generate(self, prompt: str) -> bytes: ...


class TextProvider(ProviderBase):
    _registry: ClassVar[dict[str, type["TextProvider"]]] = {}

    @abstractmethod
    def generate(self, prompt: str) -> str: ...


class ContextProvider(ProviderBase):
    _registry: ClassVar[dict[str, type["ContextProvider"]]] = {}

    @abstractmethod
    def generate(self, target_date: date) -> list[dict]: ...


class TextToIntProvider(ProviderBase):
    _registry: ClassVar[dict[str, type["TextToIntProvider"]]] = {}

    @abstractmethod
    def generate(self, prompt: str, entries: list[str]) -> int: ...


class TextToEmojiProvider(ProviderBase):
    _registry: ClassVar[dict[str, type["TextToEmojiProvider"]]] = {}

    @abstractmethod
    def generate(self, prompt: str) -> str: ...


class PublishingProvider(ProviderBase):
    _registry: ClassVar[dict[str, type["PublishingProvider"]]] = {}

    @abstractmethod
    def publish(self, image_path: str | None, caption: str | None) -> dict: ...
