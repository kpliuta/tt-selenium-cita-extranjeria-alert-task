from __future__ import annotations

from unittest.mock import MagicMock, mock_open, patch

import pytest
import requests

from selenium_scraper.notifier import TelegramNotifier


@pytest.fixture
def notifier() -> TelegramNotifier:
    return TelegramNotifier(
        bot_token="test_token",
        chat_id="test_chat",
        base_url="https://api.telegram.org/bot<your_bot_token>",
    )


class TestTelegramNotifier:
    def test_init_raises_on_missing_token(self) -> None:
        with pytest.raises(ValueError, match="Telegram API base URL"):
            TelegramNotifier(bot_token="", chat_id="test_chat")

    def test_init_raises_on_missing_chat_id(self) -> None:
        with pytest.raises(ValueError, match="Telegram API base URL"):
            TelegramNotifier(bot_token="test_token", chat_id="")

    def test_init_raises_on_missing_base_url(self) -> None:
        with pytest.raises(ValueError, match="Telegram API base URL"):
            TelegramNotifier(bot_token="test_token", chat_id="test_chat", base_url="")

    @patch("selenium_scraper.notifier.requests.post")
    def test_send_message_success(
        self, mock_post: MagicMock, notifier: TelegramNotifier
    ) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notifier.send_message("Hello")

        mock_post.assert_called_once_with(
            "https://api.telegram.org/bottest_token/sendMessage",
            data={"chat_id": "test_chat", "text": "Hello"},
        )

    @patch("selenium_scraper.notifier.requests.post")
    def test_send_message_failure(
        self, mock_post: MagicMock, notifier: TelegramNotifier
    ) -> None:
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        notifier.send_message("Hello")

        mock_post.assert_called_once()

    @patch("selenium_scraper.notifier.requests.post")
    def test_send_screenshot_success(
        self, mock_post: MagicMock, notifier: TelegramNotifier
    ) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        with patch("builtins.open", mock_open(read_data=b"fake_image_data")) as mock_file:
            notifier.send_screenshot("/fake/path.png")

            mock_file.assert_called_once_with("/fake/path.png", "rb")
            mock_post.assert_called_once_with(
                "https://api.telegram.org/bottest_token/sendPhoto",
                data={"chat_id": "test_chat"},
                files={"photo": mock_file.return_value},
            )

    @patch("selenium_scraper.notifier.requests.post")
    def test_send_screenshot_failure(
        self, mock_post: MagicMock, notifier: TelegramNotifier
    ) -> None:
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        with patch("builtins.open", mock_open(read_data=b"fake")):
            notifier.send_screenshot("/fake/path.png")
        mock_post.assert_called_once()
