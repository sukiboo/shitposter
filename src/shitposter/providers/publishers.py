import os
from pathlib import PurePath

import httpx
import tweepy  # type: ignore[import-untyped]

from shitposter.providers.base import PublishingProvider


class PlaceholderPublisher(PublishingProvider):
    name = "placeholder"

    def __init__(self, **kwargs):
        pass

    def metadata(self) -> dict:
        return super().metadata()

    def publish(self, image_path: str | None, caption: str | None) -> dict:
        return {"ok": True, "result": {"message_id": 0}}


class TelegramPublisher(PublishingProvider):
    name = "telegram"
    env_prefix = "TELEGRAM_CHANNEL"

    def __init__(self, **kwargs):
        self.bot_token = os.environ[f"{self.env_prefix}_BOT_TOKEN"]
        self.chat_id = os.environ[f"{self.env_prefix}_CHAT_ID"]
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def metadata(self) -> dict:
        return {**super().metadata(), "chat_id": self.chat_id}

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


class TelegramDebugPublisher(TelegramPublisher):
    name = "debug"
    env_prefix = "TELEGRAM_DEBUG"


class TwitterPublisher(PublishingProvider):
    name = "twitter"

    def __init__(self, **kwargs):
        consumer_key = os.environ["TWITTER_CONSUMER_KEY"]
        consumer_secret = os.environ["TWITTER_CONSUMER_SECRET"]
        access_token = os.environ["TWITTER_ACCESS_TOKEN"]
        access_token_secret = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]
        auth = tweepy.OAuth1UserHandler(
            consumer_key,
            consumer_secret,
            access_token,
            access_token_secret,
        )
        self._api = tweepy.API(auth)
        self._client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )
        me = self._client.get_me()
        self._username: str = me.data.username if me.data else "unknown"  # type: ignore

    def metadata(self) -> dict:
        return {**super().metadata(), "username": self._username}

    def publish(self, image_path: str | None, caption: str | None) -> dict:
        media_ids = None
        if image_path:
            media = self._api.media_upload(image_path)
            media_ids = [media.media_id]
        response = self._client.create_tweet(text=caption or "", media_ids=media_ids)
        return {"ok": True, "result": {"message_id": response.data["id"]}}  # type: ignore
