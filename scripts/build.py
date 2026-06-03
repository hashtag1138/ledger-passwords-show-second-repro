#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

from utils import ReproError, ensure_dir, ensure_prereqs, load_lock, remove_tree, repo_root, run, write_json


def clone_upstream(upstream_dir: Path, repo_url: str, commit: str) -> None:
    if not upstream_dir.exists():
        ensure_dir(upstream_dir.parent)
        run(["git", "clone", repo_url, str(upstream_dir)])
    run(["git", "fetch", "--tags", "origin"], cwd=upstream_dir)
    run(["git", "checkout", "--force", commit], cwd=upstream_dir)
    run(["git", "clean", "-fdx"], cwd=upstream_dir)


def prepare_local_clone(source_repo: Path, destination: Path, commit: str) -> None:
    remove_tree(destination)
    run(["git", "clone", "--shared", str(source_repo), str(destination)])
    run(["git", "checkout", "--force", commit], cwd=destination)
    run(["git", "clean", "-fdx"], cwd=destination)


def apply_patch(worktree: Path, patch_file: Path) -> None:
    patch_path = patch_file.resolve()
    run(["git", "apply", "--check", str(patch_path)], cwd=worktree)
    run(["git", "apply", str(patch_path)], cwd=worktree)


def build_app(source_dir: Path, builder_image: str, make_flags: list[str]) -> Path:
    build_command = " ".join(make_flags)
    run(
        [
            "docker",
            "run",
            "--rm",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "-v",
            f"{source_dir}:/app",
            "-w",
            "/app",
            builder_image,
            "bash",
            "-lc",
            f"BOLOS_SDK=$NANOSP_SDK make all {build_command}",
        ]
    )
    app_elf = source_dir / "bin" / "app.elf"
    if not app_elf.exists():
        raise ReproError(f"Build succeeded but missing ELF: {app_elf}")
    return app_elf


def main() -> None:
    ensure_prereqs()
    root = repo_root()
    lock = load_lock()

    upstream_dir = root / "third_party" / "app-passwords-upstream"
    original_dir = root / "artifacts" / "build" / "original" / "app-passwords"
    patched_dir = root / "artifacts" / "build" / "patched" / "app-passwords"
    patch_file = root / "patches" / "app-passwords" / "0001-fix-show-second-index.patch"

    clone_upstream(
        upstream_dir=upstream_dir,
        repo_url=lock["app_passwords"]["repo"],
        commit=lock["app_passwords"]["commit"],
    )

    prepare_local_clone(upstream_dir, original_dir, lock["app_passwords"]["commit"])
    prepare_local_clone(upstream_dir, patched_dir, lock["app_passwords"]["commit"])
    apply_patch(patched_dir, patch_file)

    make_flags = list(lock["build"]["make_flags"])
    if lock["build"]["populate"]:
        make_flags.append("POPULATE=1")

    original_elf = build_app(original_dir, lock["docker_images"]["builder"], make_flags)
    patched_elf = build_app(patched_dir, lock["docker_images"]["builder"], make_flags)

    manifest = {
        "upstream_repo": lock["app_passwords"]["repo"],
        "upstream_commit": lock["app_passwords"]["commit"],
        "builder_image": lock["docker_images"]["builder"],
        "speculos_image": lock["docker_images"]["speculos"],
        "make_flags": make_flags,
        "original_source_dir": str(original_dir),
        "patched_source_dir": str(patched_dir),
        "original_elf": str(original_elf),
        "patched_elf": str(patched_elf),
        "patch_file": str(patch_file),
    }
    write_json(root / "artifacts" / "build" / "manifest.json", manifest)

    print("")
    print("Build complete.")
    print(f"Original ELF: {original_elf}")
    print(f"Patched ELF:  {patched_elf}")
    print(f"Manifest:     {root / 'artifacts' / 'build' / 'manifest.json'}")


if __name__ == "__main__":
    main()
