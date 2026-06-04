#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

from utils import (
    ensure_prereqs,
    fix_slug,
    load_lock,
    parse_fixes_arg,
    remove_tree,
    repo_root,
    resolve_fix_docs,
    resolve_patch_files,
    run,
    write_json,
    ReproError,
    ensure_dir,
)


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


def apply_patch_series(worktree: Path, patch_files: list[Path]) -> None:
    for patch_file in patch_files:
        run(["git", "apply", "--check", str(patch_file)], cwd=worktree)
        run(["git", "apply", str(patch_file)], cwd=worktree)


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build upstream and candidate app-passwords variants for a selected fix set.",
    )
    parser.add_argument(
        "--fixes",
        default=None,
        help=(
            "Comma-separated fix ids to apply to the candidate variant. "
            "Examples: show-second-index, azerty-right-alt, "
            "show-second-index,azerty-right-alt"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_prereqs()
    root = repo_root()
    lock = load_lock()
    selected_fixes = parse_fixes_arg(args.fixes)
    selected_slug = fix_slug(selected_fixes)
    selected_patch_files = resolve_patch_files(selected_fixes)

    upstream_dir = root / "third_party" / "app-passwords-upstream"
    upstream_build_dir = root / "artifacts" / "build" / "upstream" / "app-passwords"
    candidate_build_dir = root / "artifacts" / "build" / f"candidate-{selected_slug}" / "app-passwords"

    clone_upstream(
        upstream_dir=upstream_dir,
        repo_url=lock["app_passwords"]["repo"],
        commit=lock["app_passwords"]["commit"],
    )

    prepare_local_clone(upstream_dir, upstream_build_dir, lock["app_passwords"]["commit"])
    prepare_local_clone(upstream_dir, candidate_build_dir, lock["app_passwords"]["commit"])
    apply_patch_series(candidate_build_dir, selected_patch_files)

    make_flags = list(lock["build"]["make_flags"])
    if lock["build"]["populate"]:
        make_flags.append("POPULATE=1")

    upstream_elf = build_app(upstream_build_dir, lock["docker_images"]["builder"], make_flags)
    candidate_elf = build_app(candidate_build_dir, lock["docker_images"]["builder"], make_flags)

    manifest = {
        "upstream_repo": lock["app_passwords"]["repo"],
        "upstream_commit": lock["app_passwords"]["commit"],
        "builder_image": lock["docker_images"]["builder"],
        "speculos_image": lock["docker_images"]["speculos"],
        "make_flags": make_flags,
        "candidate_fixes": list(selected_fixes),
        "candidate_slug": selected_slug,
        "candidate_docs": resolve_fix_docs(selected_fixes),
        "patch_files": [str(path.relative_to(root)) for path in selected_patch_files],
        "variants": {
            "upstream": {
                "source_dir": str(upstream_build_dir),
                "elf": str(upstream_elf),
                "fixes": [],
                "slug": "upstream",
            },
            "candidate": {
                "source_dir": str(candidate_build_dir),
                "elf": str(candidate_elf),
                "fixes": list(selected_fixes),
                "slug": selected_slug,
            },
        },
    }
    write_json(root / "artifacts" / "build" / "manifest.json", manifest)

    print("")
    print("Build complete.")
    print(f"Candidate fixes: {', '.join(selected_fixes) if selected_fixes else 'none'}")
    print(f"Upstream ELF:   {upstream_elf}")
    print(f"Candidate ELF:  {candidate_elf}")
    print(f"Manifest:       {root / 'artifacts' / 'build' / 'manifest.json'}")


if __name__ == "__main__":
    main()
