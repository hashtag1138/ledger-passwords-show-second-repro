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


def repo_root() -> Path:
    return ROOT


def load_lock() -> dict[str, Any]:
    return json.loads((ROOT / "repro.lock.json").read_text(encoding="utf-8"))


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
