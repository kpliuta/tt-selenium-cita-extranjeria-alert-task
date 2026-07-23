from __future__ import annotations

import logging
from typing import Callable, List, Tuple

from .scraper_context import ScraperContext

logger = logging.getLogger(__name__)

Step = Tuple[str, Callable[[ScraperContext], None]]


class ScraperRunner:
    """The core scraper class that runs the web scraping steps."""

    def __init__(
        self,
        context: ScraperContext,
        steps: List[Step],
        notify_on_error: bool = False,
    ) -> None:
        self._context = context
        self._steps = steps
        self._notify_on_error = notify_on_error

    @property
    def context(self) -> ScraperContext:
        return self._context

    def run(self) -> None:
        try:
            for name, func in self._steps:
                logger.info("Executing step: %s", name)
                func(self._context)
        except Exception as e:
            logger.error("An unexpected error occurred during execution: %s", e)
            if self._notify_on_error:
                self._context.send_message(f"An unexpected error occurred: {e}")
                path = self._context.capture_screenshot()
                if self._context.is_send_screenshot:
                    self._context.send_screenshot(path)
            raise
        finally:
            logger.info("Execution finished, quitting driver")
            self._context.driver.quit()
