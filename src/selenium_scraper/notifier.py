from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class Notifier(ABC):
    """Abstract base class for a notifier."""

    @abstractmethod
    def send_message(self, message: str) -> None:
        pass

    @abstractmethod
    def send_screenshot(self, path: Path) -> None:
        pass


class TelegramNotifier(Notifier):
    """A notifier implementation for Telegram."""

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        base_url: str = "https://api.telegram.org/bot<your_bot_token>",
    ) -> None:
        if not bot_token or not chat_id or not base_url:
            raise ValueError("Telegram API base URL, bot token, and chat ID must be provided.")

        self._base_url = base_url.replace("<your_bot_token>", bot_token)
        self._chat_id = chat_id
        self._send_message_url = f"{self._base_url}/sendMessage"
        self._send_photo_url = f"{self._base_url}/sendPhoto"

    def send_message(self, message: str) -> None:
        try:
            response = requests.post(
                self._send_message_url,
                data={"chat_id": self._chat_id, "text": message},
            )
            response.raise_for_status()
            logger.info("Telegram notification sent: %s", message)
        except requests.exceptions.RequestException as e:
            logger.error("Error sending Telegram notification: %s", e)

    def send_screenshot(self, path: Path) -> None:
        try:
            with open(path, "rb") as photo:
                response = requests.post(
                    self._send_photo_url,
                    data={"chat_id": self._chat_id},
                    files={"photo": photo},
                )
            response.raise_for_status()
            logger.info("Telegram screenshot sent: %s", path)
        except requests.exceptions.RequestException as e:
            logger.error("Error sending Telegram screenshot: %s", e)
