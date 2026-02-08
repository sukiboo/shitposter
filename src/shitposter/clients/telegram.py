from pathlib import Path

import httpx


class TelegramClient:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def publish(self, image_path: Path | None, caption: str | None) -> dict:
        if image_path:
            return self._send_photo(image_path, caption)
        return self._send_message(caption)

    def _send_photo(self, image_path: Path, caption: str | None) -> dict:
        with open(image_path, "rb") as f:
            files = {"photo": (image_path.name, f, "image/png")}
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
