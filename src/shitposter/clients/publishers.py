import os
from pathlib import PurePath

import httpx

from shitposter.clients.base import PublishingProvider


class PlaceholderPublisher(PublishingProvider):
    def __init__(self, **kwargs):
        pass

    def metadata(self) -> dict:
        return {"provider": "placeholder", **super().metadata()}

    def publish(self, image_path: str | None, caption: str | None) -> dict:
        return {"ok": True, "result": {"message_id": 0}}


class TelegramPublisher(PublishingProvider):
    def __init__(self, *, debug: bool = False, **kwargs):
        prefix = "TELEGRAM_DEBUG" if debug else "TELEGRAM_CHANNEL"
        self.bot_token = os.environ[f"{prefix}_BOT_TOKEN"]
        self.chat_id = os.environ[f"{prefix}_CHAT_ID"]
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def metadata(self) -> dict:
        return {"provider": "telegram", "chat_id": self.chat_id, **super().metadata()}

    def publish(self, image_path: str | None, caption: str | None) -> dict:
        if image_path:
            return self._send_photo(image_path, caption)
        return self._send_message(caption)

    def _send_photo(self, image_path: str, caption: str | None) -> dict:
        with open(image_path, "rb") as f:
            files = {"photo": (PurePath(image_path).name, f, "image/png")}
            data: dict[str, str] = {"chat_id": self.chat_id}
            if caption:
                data["caption"] = caption
            resp = httpx.post(f"{self.base_url}/sendPhoto", data=data, files=files, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _send_message(self, text: str | None) -> dict:
        resp = httpx.post(
            f"{self.base_url}/sendMessage",
            json={"chat_id": self.chat_id, "text": text or ""},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


PUBLISHERS: dict[str, type[PublishingProvider]] = {
    "placeholder": PlaceholderPublisher,
    "telegram": TelegramPublisher,
}
