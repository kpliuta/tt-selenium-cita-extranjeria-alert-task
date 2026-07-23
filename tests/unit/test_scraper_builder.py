from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock, patch

import pytest

from selenium_scraper.scraper_builder import ScraperBuilder


class TestGetDefaultDriverOptions:
    def test_returns_options(self) -> None:
        options = ScraperBuilder.get_default_driver_options()
        assert options is not None

    def test_sets_default_preferences(self) -> None:
        options = ScraperBuilder.get_default_driver_options()
        prefs = {}
        for key in (
            "extensions.enabledScopes",
            "dom.webdriver.enabled",
            "layers.acceleration.disabled",
            "media.peerconnection.enabled",
            "devtools.jsonview.enabled",
            "privacy.trackingprotection.enabled",
            "browser.safebrowsing.enabled",
            "browser.safebrowsing.malware.enabled",
            "browser.safebrowsing.phishing.enabled",
            "intl.accept_languages",
        ):
            prefs[key] = options.preferences[key]
        assert prefs["dom.webdriver.enabled"] is False
        assert prefs["intl.accept_languages"] == "en-US, en;q=0.5"


class TestScraperBuilder:
    def test_with_send_screenshot(self) -> None:
        builder = ScraperBuilder()
        result = builder.with_send_screenshot(True)
        assert result is builder
        assert builder._is_send_screenshot is True

    def test_with_screenshots_dir(self) -> None:
        builder = ScraperBuilder()
        result = builder.with_screenshots_dir(Path("/tmp/screenshots"))
        assert result is builder
        assert builder._screenshots_dir == Path("/tmp/screenshots")

    def test_with_notify_on_error(self) -> None:
        builder = ScraperBuilder()
        result = builder.with_notify_on_error(True)
        assert result is builder
        assert builder._notify_on_error is True

    def test_with_user_agent(self) -> None:
        builder = ScraperBuilder()
        result = builder.with_user_agent("Custom UA")
        assert result is builder
        assert builder._user_agent == "Custom UA"

    def test_with_user_agent_file(self) -> None:
        builder = ScraperBuilder()
        result = builder.with_user_agent_file(Path("/path/to/uas.txt"))
        assert result is builder
        assert builder._user_agent_file == Path("/path/to/uas.txt")

    def test_with_step(self) -> None:
        builder = ScraperBuilder()
        func = lambda ctx: None
        result = builder.with_step("Step 1", func)
        assert result is builder
        assert len(builder._steps) == 1
        assert builder._steps[0] == ("Step 1", func)

    def test_with_notifier(self) -> None:
        builder = ScraperBuilder()
        notifier = MagicMock()
        result = builder.with_notifier(notifier)
        assert result is builder
        assert builder._notifiers == [notifier]

    def test_with_state(self) -> None:
        builder = ScraperBuilder()
        state = {"key": "val"}
        result = builder.with_state(state)
        assert result is builder
        assert builder._state == state

    def test_apply_user_agent_manual_override(self) -> None:
        builder = ScraperBuilder()
        builder.with_user_agent("Manual UA")
        options = MagicMock()
        builder._apply_user_agent(options)
        options.set_preference.assert_called_once_with(
            "general.useragent.override", "Manual UA"
        )

    @patch("selenium_scraper.scraper_builder.random.choice")
    def test_apply_user_agent_file(self, mock_choice: MagicMock) -> None:
        mock_choice.return_value = "File UA"
        with NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("UA1\nFile UA\nUA3\n")
            ua_path = f.name
        try:
            builder = ScraperBuilder()
            builder.with_user_agent_file(Path(ua_path))
            options = MagicMock()
            builder._apply_user_agent(options)
            options.set_preference.assert_called_once_with(
                "general.useragent.override", "File UA"
            )
        finally:
            Path(ua_path).unlink()

    @patch("selenium_scraper.scraper_builder.random.choice")
    def test_apply_user_agent_manual_takes_precedence_over_file(
        self, mock_choice: MagicMock
    ) -> None:
        mock_choice.return_value = "File UA"
        builder = ScraperBuilder()
        builder.with_user_agent("Manual UA").with_user_agent_file(Path("/fake/path.txt"))
        options = MagicMock()
        builder._apply_user_agent(options)
        options.set_preference.assert_called_once_with(
            "general.useragent.override", "Manual UA"
        )

    @patch("selenium_scraper.scraper_builder.ScraperRunner")
    @patch("selenium_scraper.scraper_builder.webdriver.Firefox")
    def test_build_creates_runner(
        self,
        mock_firefox: MagicMock,
        mock_runner: MagicMock,
    ) -> None:
        builder = ScraperBuilder()
        notifier = MagicMock()
        func = lambda ctx: None
        builder.with_notifier(notifier)
        builder.with_step("step1", func)
        builder.with_send_screenshot(True)
        runner = builder.build()
        assert runner is not None
        mock_runner.assert_called_once()
        args, kwargs = mock_runner.call_args
        assert "context" in kwargs
        assert kwargs["notify_on_error"] is False
        assert kwargs["steps"] == [("step1", func)]

    @patch("selenium_scraper.scraper_builder.ScraperRunner")
    @patch("selenium_scraper.scraper_builder.webdriver.Firefox")
    def test_build_raises_on_second_call(
        self,
        mock_firefox: MagicMock,
        mock_runner: MagicMock,
    ) -> None:
        builder = ScraperBuilder()
        builder.with_step("step1", lambda ctx: None)
        builder._apply_user_agent = MagicMock()
        builder.build()
        with pytest.raises(RuntimeError, match="build.*only.*once"):
            builder.build()
