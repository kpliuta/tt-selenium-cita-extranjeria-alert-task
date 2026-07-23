[//]: # (identity)

- You are an experienced Python engineer.
- MEMORY.md is your cross-session memory for this project. Read it at session start to get up to speed fast. If it doesn't exist, analyze the project file by file and create it.
- If something is unclear, analyze the codebase deeper and update MEMORY.md.
- When introducing new conventions, libraries, patterns, or project structure changes, update MEMORY.md immediately.
- Keep AGENTS.md and MEMORY.md up to date — update after any codebase change.
- Stay consistent with existing patterns and code style.

[//]: # (workflow)

- Ask before starting if anything is unclear.
- FOLLOW TDD. Cover new/modified logic with unit tests; run after each change — must be green.
- Delete all unused code (methods, classes, files, imports).
- Run `poetry run mypy src/` and `poetry run autoflake --remove-all-unused-imports --ignore-init-module-imports --in-place --recursive src/` after every change — both must pass/be clean.
- Update README.md for user-visible changes.
- Update CHANGELOG.md (add entries under `## [Unreleased]`) and BACKLOG.md (move completed items, update status) for every commit.
- Use all the skills under .agent/skills/* where applicable.
- The application (termux-tasker) that runs the runner resides in ../termux-tasker.
- The runner (tt-selenium-runner) resides in ../tt-selenium-runner.
- The original monitor this task is based on resides in ../cita-previa-extranjeria-monitor.
- The selenium-scraper framework resides in ../selenium-scraper.

[//]: # (python)

- `from __future__ import annotations` at the top of every file.
- Type hints on all function signatures and dataclass fields.
- Early returns / guard clauses for error handling; happy path last.
- Descriptive variable names with auxiliary verbs: `is_active`, `has_permission`.
- `@dataclass` for data models.
- `Path` for all filesystem paths — never raw strings.
- Prefer modules+functions over classes.

[//]: # (testing — unit)

- Unit tests in `tests/unit/` — plain pytest.
- Mock external dependencies; avoid `torch`.
- All tests run in parallel by default (`-n auto`). For serial debugging: `pytest -n 0`.
