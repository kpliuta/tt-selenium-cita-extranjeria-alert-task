from __future__ import annotations

import logging
import random
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from selenium.common import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

from .notifier import Notifier

logger = logging.getLogger(__name__)


class ScraperContext:
    """Context passed through scraping steps, providing driver, state, notifiers,
    and convenience methods for element interaction.
    """

    def __init__(
        self,
        driver: WebDriver,
        notifiers: List[Notifier],
        state: Dict[str, Any] | None = None,
        is_send_screenshot: bool = False,
        screenshots_dir: Path | None = None,
    ) -> None:
        self._driver = driver
        self._notifiers = notifiers
        self._state: Dict[str, Any] = state or {}
        self._is_send_screenshot = is_send_screenshot
        self._screenshots_dir = screenshots_dir

    @property
    def driver(self) -> WebDriver:
        """Selenium WebDriver instance for browser interaction."""
        return self._driver

    @property
    def is_send_screenshot(self) -> bool:
        """Whether screenshots should be captured and sent."""
        return self._is_send_screenshot

    def get_state(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from shared step state."""
        return self._state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        """Store a value in shared step state."""
        self._state[key] = value

    def send_message(self, message: str) -> None:
        """Send a text message through all registered notifiers."""
        for notifier in self._notifiers:
            notifier.send_message(message)

    def send_screenshot(self, screenshot_path: Path | None = None) -> None:
        """Send a screenshot through all notifiers.

        If screenshot_path is provided, it is sent directly.
        Otherwise, a screenshot is captured to a temporary file,
        sent, and is removed after.

        Typical usage is to call capture_screenshot() first to save
        a persistent copy, then pass the returned path here.
        """
        if not self._is_send_screenshot:
            logger.warning("send_screenshot called but is_send_screenshot is False")
            return

        if screenshot_path is not None:
            path = screenshot_path
        else:
            path = self._capture_temp_screenshot()

        try:
            for notifier in self._notifiers:
                notifier.send_screenshot(path)
        finally:
            if screenshot_path is None:
                path.unlink(missing_ok=True)

    def _capture_temp_screenshot(self) -> Path:
        """Capture a screenshot to a temp file and return its path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tmp_path = Path(tempfile.gettempdir(), f"{timestamp}.png")
        self._driver.save_screenshot(str(tmp_path))
        return tmp_path

    def capture_screenshot(self) -> Optional[Path]:
        """Save a screenshot with timestamp to screenshots_dir.

        Returns the path to the saved screenshot, or None if
        screenshots_dir is not configured.
        """
        if not self._screenshots_dir:
            logger.warning("capture_screenshot called but screenshots_dir is not set")
            return None

        self._screenshots_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self._screenshots_dir / f"{timestamp}.png"
        self._driver.save_screenshot(str(path))
        return path

    def get_element(self, locator: Tuple[str, str], timeout: int = 10) -> Any:
        """Wait for and return a visible element matching locator."""
        logger.debug("Get element %s='%s'", locator[0], locator[1])
        wait = WebDriverWait(self._driver, timeout)
        return wait.until(ec.visibility_of_element_located(locator))

    def get_optional_element(
        self, locator: Tuple[str, str], timeout: int = 10
    ) -> Optional[Any]:
        """Return element if visible within timeout, else None."""
        try:
            return self.get_element(locator, timeout)
        except TimeoutException:
            return None

    def click_element(self, locator: Tuple[str, str], timeout: int = 10) -> None:
        """Click a visible element."""
        logger.debug("Click element %s='%s'", locator[0], locator[1])
        element = self.get_element(locator, timeout)
        element.click()

    def send_keys(
        self, locator: Tuple[str, str], text: str, timeout: int = 10
    ) -> None:
        """Send keys to a visible element."""
        logger.debug("Send keys to element %s='%s'", locator[0], locator[1])
        element = self.get_element(locator, timeout)
        element.send_keys(text)

    def select_option_by_text(
        self, locator: Tuple[str, str], option_text: str, timeout: int = 10
    ) -> None:
        """Select a dropdown option by its visible text."""
        logger.debug("Select '%s' in %s='%s'", option_text, locator[0], locator[1])
        dropdown = self.get_element(locator, timeout)
        select = Select(dropdown)
        select.select_by_visible_text(option_text)

    def random_sleep(
        self, x: Union[int, float], y: Union[int, float]
    ) -> None:
        """Sleep for a random duration between x and y milliseconds."""
        random_duration = random.uniform(x, y) / 1000
        logger.debug("Sleep for %.2f seconds", random_duration)
        time.sleep(random_duration)
