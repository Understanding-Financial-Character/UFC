# Backend Ruff EXE002 On Windows Bind Mount

## Symptoms

Running this command on Windows can report `EXE002 The file is executable but no shebang is present` for many Python files:

```bash
docker compose -f compose.yaml -f compose.dev.yaml run --rm backend ruff check app tests
```

## Cause

The repository files may be normal `100644` in Git, but Docker Desktop bind mounts from Windows can present mounted files inside Linux containers with executable bits. Ruff's executable-file rule then treats ordinary Python modules as executable scripts.

## Checks

Confirm Git file modes from the host:

```bash
git ls-files -s backend/app/main.py backend/tests/test_foundation.py
```

Expected tracked mode is `100644`.

## Workarounds

- Prefer running the backend lint command in a Linux filesystem environment where bind-mounted file modes are preserved.
- If this becomes a recurring Windows-only blocker, record a team decision before changing Ruff configuration to ignore `EXE002` globally.
- Do not mass-toggle file modes from Windows unless `git ls-files -s` shows actual tracked executable bits.
