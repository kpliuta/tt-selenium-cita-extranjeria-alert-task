from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, create_autospec

import pytest

from selenium_scraper.notifier import Notifier
from selenium_scraper.scraper_context import ScraperContext


@pytest.fixture
def mock_notifier() -> MagicMock:
    return create_autospec(Notifier, instance=True)


@pytest.fixture
def mock_driver() -> MagicMock:
    return MagicMock()


@pytest.fixture
def context(mock_driver: MagicMock, mock_notifier: MagicMock) -> ScraperContext:
    return ScraperContext(
        driver=mock_driver,
        notifiers=[mock_notifier],
        state={"key1": "val1"},
        is_send_screenshot=True,
        screenshots_dir=Path("/tmp/screenshots"),
    )


class TestScraperContext:
    def test_driver_property(self, context: ScraperContext, mock_driver: MagicMock) -> None:
        assert context.driver is mock_driver

    def test_is_send_screenshot_property(self, context: ScraperContext) -> None:
        assert context.is_send_screenshot is True

    def test_get_state_existing(self, context: ScraperContext) -> None:
        assert context.get_state("key1") == "val1"

    def test_get_state_missing(self, context: ScraperContext) -> None:
        assert context.get_state("nonexistent") is None

    def test_get_state_missing_with_default(self, context: ScraperContext) -> None:
        assert context.get_state("nonexistent", "fallback") == "fallback"

    def test_set_state(self, context: ScraperContext) -> None:
        context.set_state("key2", "val2")
        assert context.get_state("key2") == "val2"

    def test_send_message_calls_notifier(
        self, context: ScraperContext, mock_notifier: MagicMock
    ) -> None:
        context.send_message("hello")
        mock_notifier.send_message.assert_called_once_with("hello")

    def test_send_message_calls_all_notifiers(
        self, mock_driver: MagicMock, mock_notifier: MagicMock
    ) -> None:
        another = create_autospec(Notifier, instance=True)
        ctx = ScraperContext(
            driver=mock_driver, notifiers=[mock_notifier, another]
        )
        ctx.send_message("test")
        mock_notifier.send_message.assert_called_once_with("test")
        another.send_message.assert_called_once_with("test")

    def test_send_screenshot_skipped_when_flag_false(
        self, mock_driver: MagicMock, mock_notifier: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        ctx = ScraperContext(
            driver=mock_driver,
            notifiers=[mock_notifier],
            is_send_screenshot=False,
        )
        with caplog.at_level(logging.WARNING):
            ctx.send_screenshot()
        assert "send_screenshot called but is_send_screenshot is False" in caplog.text
        mock_notifier.send_screenshot.assert_not_called()

    def test_send_screenshot_with_path(
        self, context: ScraperContext, mock_notifier: MagicMock
    ) -> None:
        context.send_screenshot(Path("/path/to/shot.png"))
        mock_notifier.send_screenshot.assert_called_once_with(Path("/path/to/shot.png"))

    def test_send_screenshot_captures_to_temp_when_no_path(
        self, context: ScraperContext, mock_notifier: MagicMock, mock_driver: MagicMock
    ) -> None:
        context.send_screenshot()
        assert mock_driver.save_screenshot.called
        saved_path = mock_driver.save_screenshot.call_args[0][0]
        assert saved_path.endswith(".png")
        assert not Path(saved_path).exists()
        assert mock_notifier.send_screenshot.called

    def test_is_send_screenshot_default_false(
        self, mock_driver: MagicMock, mock_notifier: MagicMock
    ) -> None:
        ctx = ScraperContext(driver=mock_driver, notifiers=[mock_notifier])
        assert ctx.is_send_screenshot is False

    def test_capture_screenshot_returns_path(
        self, context: ScraperContext, mock_driver: MagicMock
    ) -> None:
        path = context.capture_screenshot()
        assert path is not None
        assert str(path).startswith("/tmp/screenshots/")
        assert path.suffix == ".png"

    def test_capture_screenshot_warns_when_dir_not_set(
        self, mock_driver: MagicMock, mock_notifier: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        ctx = ScraperContext(
            driver=mock_driver, notifiers=[mock_notifier], screenshots_dir=None
        )
        with caplog.at_level(logging.WARNING):
            result = ctx.capture_screenshot()
        assert "capture_screenshot called but screenshots_dir is not set" in caplog.text
        assert result is None
