# tt-selenium-cita-extranjeria-alert-task

A [termux-tasker](https://github.com/kpliuta/termux-tasker) task that monitors
Spanish immigration office appointment availability and sends Telegram alerts
when a slot is found.

Designed to run under [tt-selenium-runner](https://github.com/kpliuta/tt-selenium-runner),
which manages a proot-distro Ubuntu container with VNC + Firefox for Selenium
tasks on Android via Termux.

## How It Works

The task navigates the Spanish immigration appointment portal
(`icp.administracionelectronica.gob.es`), fills in the configured personal data,
and checks for available appointment slots. When a slot is detected, it sends
a Telegram notification (and optionally a screenshot).

## Task Parameters

| Parameter                            | Description                                              | Required               |
|--------------------------------------|----------------------------------------------------------|------------------------|
| `telegram_api_url`                   | Telegram Bot API base URL                                | Yes (has default)      |
| `telegram_bot_token`                 | Telegram Bot Token                                       | Yes                    |
| `telegram_chat_id`                   | Telegram Chat ID                                         | Yes                    |
| `province`                           | Spanish province for appointment search                  | Yes                    |
| `office`                             | Office (oficina), leave empty to skip                    | No                     |
| `procedure`                          | Exact procedure/tramite string from the website dropdown | Yes                    |
| `nie`                                | Foreigner identification number (NIE)                    | Yes                    |
| `full_name`                          | Full name as on the application                          | Yes                    |
| `send_screenshot`                    | Send screenshot on appointment found (`true`/`false`)    | Yes (default: `false`) |
| `send_notifications_only_on_success` | Notify only when a slot is found (`true`/`false`)        | Yes (default: `true`)  |

## Local Development

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/)
- Firefox installed locally

### Setup

Install dev dependencies (includes mypy and autoflake):

```bash
poetry install --extras dev
```
### Configuration

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your Telegram credentials, province, NIE, and other parameters.
The `.env` file is gitignored and used only for local development.

### Running Locally

```bash
poetry run python src/main.py
```

The script reads configuration from the `.env` file. In the runner environment,
`.env` is not used — parameters are injected as `VAR_*` environment variables
by the termux-tasker task configuration.

### Run type checking and unused imports check

```bash
poetry run mypy scripts/
poetry run autoflake --remove-all-unused-imports --ignore-init-module-imports --check --recursive scripts/
```

## CI & Release

This project uses GitHub Actions for CI and automated releases. PRs must follow [Conventional Commits](https://www.conventionalcommits.org/) format — the PR title determines the version bump on merge (`fix:` → patch, `feat:` → minor, `feat!:` → major).

When a PR is merged to `main` via squash merge, the release workflow automatically bumps the version, updates the changelog, creates a git tag, and publishes a GitHub Release.

For full details, see **[CI-RELEASE.md](CI-RELEASE.md)**.