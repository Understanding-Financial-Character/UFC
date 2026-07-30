# Docker Ruff EXE002 on Windows Mounts

## Symptom

Running `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend ruff check app tests` on Windows reports `EXE002` for most Python files:

```text
EXE002 The file is executable but no shebang is present
```

## Cause

The backend source is bind-mounted from Windows into the Linux container. File executable bits can appear broader inside the container than they do in the working tree, so ruff treats ordinary Python modules as executable scripts.

## Resolution

The backend ruff configuration ignores `EXE002`. This keeps lint focused on code quality checks that are stable across Windows bind mounts. Python entrypoint scripts that truly need executable behavior should still include a shebang and be reviewed separately.
