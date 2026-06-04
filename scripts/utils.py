from __future__ import annotations

import json
import os
import shlex
import shutil
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ReproError(RuntimeError):
    pass


ROOT = Path(__file__).resolve().parents[1]
FIX_CATALOG_PATH = ROOT / "patches" / "app-passwords" / "fix-catalog.json"


def repo_root() -> Path:
    return ROOT


def load_lock() -> dict[str, Any]:
    return json.loads((ROOT / "repro.lock.json").read_text(encoding="utf-8"))


def load_fix_catalog() -> dict[str, Any]:
    return json.loads(FIX_CATALOG_PATH.read_text(encoding="utf-8"))


def available_fixes() -> dict[str, dict[str, Any]]:
    return load_fix_catalog()["fixes"]


def default_candidate_fixes() -> tuple[str, ...]:
    return tuple(load_fix_catalog()["default_candidate_fixes"])


def candidate_base_patch_files() -> list[Path]:
    catalog = load_fix_catalog().get("candidate_base", {})
    patch_files: list[Path] = []
    for relative in catalog.get("patch_files", []):
        patch_path = (ROOT / relative).resolve()
        if patch_path not in patch_files:
            patch_files.append(patch_path)
    return patch_files


def candidate_base_docs() -> list[str]:
    catalog = load_fix_catalog().get("candidate_base", {})
    docs: list[str] = []
    for relative in catalog.get("docs", []):
        if relative not in docs:
            docs.append(relative)
    return docs


def parse_fixes_arg(raw: str | None) -> tuple[str, ...]:
    fixes = default_candidate_fixes() if raw is None else tuple(part.strip() for part in raw.split(",") if part.strip())
    unknown = sorted(set(fixes) - set(available_fixes()))
    if unknown:
        raise ReproError(f"Unknown fixes: {', '.join(unknown)}")
    return tuple(dict.fromkeys(fixes))


def fix_slug(fixes: tuple[str, ...]) -> str:
    return "none" if not fixes else "__".join(fixes)


def resolve_patch_files(fixes: tuple[str, ...]) -> list[Path]:
    catalog = available_fixes()
    patch_files: list[Path] = list(candidate_base_patch_files())
    for fix in fixes:
        for relative in catalog[fix]["patch_files"]:
            patch_path = (ROOT / relative).resolve()
            if patch_path not in patch_files:
                patch_files.append(patch_path)
    return patch_files


def resolve_fix_docs(fixes: tuple[str, ...]) -> list[str]:
    catalog = available_fixes()
    docs: list[str] = list(candidate_base_docs())
    for fix in fixes:
        for relative in catalog[fix].get("docs", []):
            if relative not in docs:
                docs.append(relative)
    return docs


def ensure_command(name: str) -> None:
    if shutil.which(name) is None:
        raise ReproError(f"Required command not found in PATH: {name}")


def ensure_prereqs() -> None:
    for command in ("git", "docker", "python3"):
        ensure_command(command)


def quote_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    capture_output: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    print(f"$ {quote_command(command)}")
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=merged_env,
        text=True,
        capture_output=capture_output,
        check=False,
    )
    if check and completed.returncode != 0:
        message = (
            f"Command failed with exit code {completed.returncode}: {quote_command(command)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
        raise ReproError(message)
    return completed


def remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def copy_tree(src: Path, dst: Path) -> None:
    remove_tree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
