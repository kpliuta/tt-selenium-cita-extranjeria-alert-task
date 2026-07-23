from __future__ import annotations

import logging
import platform
import random
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

from .notifier import Notifier
from .scraper_context import ScraperContext
from .scraper_runner import ScraperRunner

logger = logging.getLogger(__name__)

StepFunction = Callable[[ScraperContext], None]
Step = Tuple[str, StepFunction]


class ScraperBuilder:
    """A builder for constructing the ScraperRunner instance."""

    @staticmethod
    def get_default_driver_options() -> Options:
        """Return Firefox options with anti-detection and automation-friendly preferences."""
        options = Options()
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")

        # disable all extension install sources
        options.set_preference("extensions.enabledScopes", 0)
        # mask automated browser flag
        options.set_preference("dom.webdriver.enabled", False)
        # reduce GPU use in headless/VNC
        options.set_preference("layers.acceleration.disabled", True)
        # block WebRTC to reduce fingerprinting
        options.set_preference("media.peerconnection.enabled", False)
        # disable JSON viewer to simplify page load
        options.set_preference("devtools.jsonview.enabled", False)
        # basic tracking protection
        options.set_preference("privacy.trackingprotection.enabled", True)
        # disable safe browsing malware checks
        options.set_preference("browser.safebrowsing.enabled", False)
        options.set_preference("browser.safebrowsing.malware.enabled", False)
        options.set_preference("browser.safebrowsing.phishing.enabled", False)
        # consistent language header
        options.set_preference("intl.accept_languages", "en-US, en;q=0.5")
        return options

    def __init__(self) -> None:
        self._steps: List[Step] = []
        self._notifiers: List[Notifier] = []
        self._state: Dict[str, Any] = {}
        self._driver_options: Optional[Options] = None
        self._is_send_screenshot: bool = False
        self._screenshots_dir: Path | None = None
        self._notify_on_error: bool = False
        self._user_agent_file: Path | None = None
        self._user_agent: str | None = None
        self._built: bool = False

    def with_step(self, name: str, func: StepFunction) -> ScraperBuilder:
        self._steps.append((name, func))
        return self

    def with_notifier(self, notifier: Notifier) -> ScraperBuilder:
        self._notifiers.append(notifier)
        return self

    def with_state(self, state: Dict[str, Any]) -> ScraperBuilder:
        self._state = state
        return self

    def with_driver_options(self, options: Options) -> ScraperBuilder:
        self._driver_options = options
        return self

    def with_send_screenshot(self, flag: bool) -> ScraperBuilder:
        self._is_send_screenshot = flag
        return self

    def with_screenshots_dir(self, path: Path) -> ScraperBuilder:
        self._screenshots_dir = path
        return self

    def with_notify_on_error(self, flag: bool) -> ScraperBuilder:
        self._notify_on_error = flag
        return self

    def with_user_agent_file(self, path: Path) -> ScraperBuilder:
        self._user_agent_file = path
        return self

    def with_user_agent(self, user_agent: str) -> ScraperBuilder:
        self._user_agent = user_agent
        return self

    def build(self) -> ScraperRunner:
        if self._built:
            raise RuntimeError("build() must only be called once")
        self._built = True

        options = self._driver_options or self.get_default_driver_options()
        self._apply_user_agent(options)
        service = FirefoxService(TermuxGeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        context = ScraperContext(
            driver=driver,
            notifiers=self._notifiers,
            state=self._state,
            is_send_screenshot=self._is_send_screenshot,
            screenshots_dir=self._screenshots_dir,
        )
        return ScraperRunner(
            context=context,
            steps=self._steps,
            notify_on_error=self._notify_on_error,
        )

    def _apply_user_agent(self, options: Options) -> None:
        """Apply user-agent override with precedence: manual > file > default.

        Manual UA (with_user_agent) takes highest precedence.
        File-based UA (with_user_agent_file) is used if no manual UA set.
        If neither is provided, the default UA baked into Options is kept.
        """
        if self._user_agent is not None:
            options.set_preference("general.useragent.override", self._user_agent)
            return
        if self._user_agent_file is not None:
            ua_list = self._user_agent_file.read_text().splitlines()
            ua_list = [line.strip() for line in ua_list if line.strip()]
            if ua_list:
                ua = random.choice(ua_list)
                logger.info("User Agent (from file): %s", ua)
                options.set_preference("general.useragent.override", ua)


class TermuxGeckoDriverManager(GeckoDriverManager):
    """Corrects OS type detection for Termux on aarch64 devices and emulators."""

    def get_os_type(self) -> str:
        if platform.machine() == "aarch64":
            return "linux-aarch64"

        os_type = super().get_os_type()
        if not os_type or "None" in str(os_type):
            return "linux64"
        return os_type
