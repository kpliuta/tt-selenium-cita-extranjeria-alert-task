from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from selenium.webdriver.common.by import By

from selenium_scraper.notifier import TelegramNotifier
from selenium_scraper.scraper_builder import ScraperBuilder
from selenium_scraper.scraper_context import ScraperContext

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def _get_env(name: str, default: str = "") -> str:
    """Reads VAR_<NAME> first (runner), then falls back to <NAME> (local .env)."""
    return os.environ.get(f"VAR_{name}", os.environ.get(name, default))


def _is_true(value: str) -> bool:
    """Return True if the lowercase string equals 'true'."""
    return value.lower() == "true"


MNT_OUTPUT_DIR: str = os.environ.get("MNT_OUTPUT_DIR", "")
TELEGRAM_BASE_URL: str = _get_env(
    "TELEGRAM_API_URL", "https://api.telegram.org/bot<your_bot_token>"
)
TELEGRAM_BOT_TOKEN: str = _get_env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: str = _get_env("TELEGRAM_CHAT_ID")
PROVINCE: str = _get_env("PROVINCE")
OFFICE: str = _get_env("OFFICE")
PROCEDURE: str = _get_env("PROCEDURE")
NIE: str = _get_env("NIE")
FULL_NAME: str = _get_env("FULL_NAME")
SEND_SCREENSHOT: str = _get_env("SEND_SCREENSHOT", "false")
SEND_NOTIFICATIONS_ONLY_ON_SUCCESS: str = _get_env(
    "SEND_NOTIFICATIONS_ONLY_ON_SUCCESS", "true"
)


def main() -> None:
    if not MNT_OUTPUT_DIR:
        logger.critical("MNT_OUTPUT_DIR environment variable is not set")
        sys.exit(1)

    output_dir = Path(MNT_OUTPUT_DIR)
    screenshots_dir = output_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    notifier = TelegramNotifier(
        bot_token=TELEGRAM_BOT_TOKEN,
        chat_id=TELEGRAM_CHAT_ID,
        base_url=TELEGRAM_BASE_URL,
    )

    scraper = (
        ScraperBuilder()
        .with_notifier(notifier)
        .with_send_screenshot(_is_true(SEND_SCREENSHOT))
        .with_screenshots_dir(screenshots_dir)
        .with_notify_on_error(True)
        .with_user_agent_file(Path("user_agents"))
        .with_step("Navigate to the appointment website", navigate_to_website)
        .with_step("Select province", select_province)
        .with_step("Select office and procedure", select_office_and_procedure)
        .with_step("Navigate through warning page", navigate_through_warning_page)
        .with_step("Fill in personal data", fill_in_personal_data)
        .with_step("Request appointment", request_appointment)
        .with_step("Verify response", verify_response)
        .build()
    )

    scraper.run()


def navigate_to_website(context: ScraperContext) -> None:
    context.driver.get("https://icp.administracionelectronica.gob.es/icpco/index")


def select_province(context: ScraperContext) -> None:
    context.select_option_by_text((By.NAME, "form"), PROVINCE)
    context.random_sleep(3000, 5000)
    context.click_element((By.ID, "btnAceptar"))


def select_office_and_procedure(context: ScraperContext) -> None:
    if OFFICE:
        context.select_option_by_text((By.NAME, "sede"), OFFICE)
        context.random_sleep(1000, 2000)
    context.select_option_by_text((By.NAME, "tramiteGrupo[0]"), PROCEDURE)
    context.random_sleep(3000, 5000)
    context.driver.execute_script("envia()")


def navigate_through_warning_page(context: ScraperContext) -> None:
    context.random_sleep(3000, 5000)
    context.driver.execute_script("document.forms[0].submit()")


def fill_in_personal_data(context: ScraperContext) -> None:
    context.send_keys((By.NAME, "txtIdCitado"), NIE)
    context.random_sleep(1000, 2000)
    context.send_keys((By.NAME, "txtDesCitado"), FULL_NAME)
    context.random_sleep(3000, 5000)
    context.driver.execute_script("envia()")


def request_appointment(context: ScraperContext) -> None:
    context.random_sleep(3000, 5000)
    context.driver.execute_script("enviar('solicitud')")


def verify_response(context: ScraperContext) -> None:
    error_message_element = context.get_optional_element((By.CLASS_NAME, "mf-msg__info"))
    if error_message_element and "En este momento no hay citas disponibles" in error_message_element.text:
        logger.info("No appointment slots available at the moment...")
        if not _is_true(SEND_NOTIFICATIONS_ONLY_ON_SUCCESS):
            context.send_message("Cita Extranjeria Alert: No appointment slots available")
        return

    logger.info("Appointment slot found!")
    context.send_message("Cita Extranjeria Alert: Appointment slot found!")
    path = context.capture_screenshot()
    if context.is_send_screenshot:
        context.send_screenshot(path)


if __name__ == "__main__":
    main()
