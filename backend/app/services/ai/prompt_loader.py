from __future__ import annotations

import hashlib
from pathlib import Path

from app.config import get_settings


def prompts_dir() -> Path:
    return Path(get_settings().prompts_dir)


def load_prompt(name: str = "diagnose_prompt.md") -> tuple[str, str, Path]:
    path = prompts_dir() / name
    if not path.is_file():
        raise FileNotFoundError("Prompt file missing: %s" % path)
    body = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return body, digest, path


def load_schema_notes() -> str:
    path = prompts_dir() / "schema.md"
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def system_prompt() -> tuple[str, str, Path]:
    body, digest, path = load_prompt("diagnose_prompt.md")
    schema = load_schema_notes()
    if schema:
        body = "%s\n\n---\n\n%s" % (body, schema)
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return body, digest, path
