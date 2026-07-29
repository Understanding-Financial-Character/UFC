from __future__ import annotations

import base64
import secrets
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = ROOT / ".env.example"
ENV_FILE = ROOT / ".env"

SECRET_KEYS = {
    "AUTH_TOKEN_SECRET": lambda: secrets.token_urlsafe(48),
    "FIELD_ENCRYPTION_KEY": lambda: base64.b64encode(secrets.token_bytes(32)).decode("ascii"),
    "FIELD_LOOKUP_HMAC_KEY": lambda: secrets.token_urlsafe(48),
    "FIELD_KEY_VERSION": lambda: "local-v1",
}

REQUIRED_DIRECTORIES = [
    ROOT / "mock-data" / "scenarios",
    ROOT / "mock-data" / "generated",
]


def main() -> None:
    ensure_docker_available()
    ensure_env_file()
    ensure_required_directories()
    print("init ok")


def ensure_docker_available() -> None:
    if shutil.which("docker") is None:
        raise SystemExit("Docker CLI was not found.")
    result = subprocess.run(
        ["docker", "info"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("Docker is not running or is not accessible.")


def ensure_env_file() -> None:
    if not ENV_EXAMPLE.exists():
        raise SystemExit(".env.example does not exist.")
    if not ENV_FILE.exists():
        ENV_FILE.write_text(ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        print("created .env from .env.example")

    values = parse_env(ENV_FILE.read_text(encoding="utf-8").splitlines())
    changed = False
    for key, generator in SECRET_KEYS.items():
        if not values.get(key):
            values[key] = generator()
            changed = True
            print(f"generated {key}")

    if changed:
        rewrite_env(values)
    else:
        print(".env already has required local secrets")


def parse_env(lines: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", maxsplit=1)
        values[key] = value
    return values


def rewrite_env(values: dict[str, str]) -> None:
    output_lines: list[str] = []
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            output_lines.append(line)
            continue
        key, _value = stripped.split("=", maxsplit=1)
        output_lines.append(f"{key}={values.get(key, '')}")
    ENV_FILE.write_text("\n".join(output_lines) + "\n", encoding="utf-8")


def ensure_required_directories() -> None:
    for directory in REQUIRED_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)
        keep = directory / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")


if __name__ == "__main__":
    main()
