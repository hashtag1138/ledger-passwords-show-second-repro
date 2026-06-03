#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from speculos_harness import SpeculosHarness
from utils import ReproError, ensure_dir, ensure_prereqs, free_port, load_lock, repo_root, utc_now_compact, write_json, write_text


@dataclass(frozen=True)
class Case:
    case_id: str
    description: str
    mode: str
    entries: tuple[str, ...]
    position: int
    expected_selected: str
    expected_original: str
    expected_patched: str


def load_cases(cases_path: Path) -> list[Case]:
    payload = json.loads(cases_path.read_text(encoding="utf-8"))
    return [
        Case(
            case_id=item["id"],
            description=item["description"],
            mode=item["mode"],
            entries=tuple(item["entries"]),
            position=int(item["position"]),
            expected_selected=item["expected_selected"],
            expected_original=item["expect"]["original"],
            expected_patched=item["expect"]["patched"],
        )
        for item in payload
    ]


def build_raw_metadatas(entries: tuple[str, ...], charset_mask: int, nickname_max_utf8_bytes: int) -> bytes:
    raw = bytearray()
    for entry in entries:
        encoded = entry.encode("utf-8")
        if not encoded:
            raise ReproError("Empty nickname is not allowed")
        if len(encoded) > nickname_max_utf8_bytes:
            raise ReproError(
                f"Nickname {entry!r} encodes to {len(encoded)} bytes, exceeds limit {nickname_max_utf8_bytes}"
            )
        raw.extend((1 + len(encoded), 0x00, charset_mask))
        raw.extend(encoded)
    raw.extend((0x00, 0x00))
    return bytes(raw)


def parse_selected_nickname(screen_text: str) -> str:
    return screen_text.split("|", 1)[0].strip()


def classify_outcome(error: Exception | None, log_tail: str) -> str:
    if error is None:
        return "ok"
    text = f"{type(error).__name__}: {error}\n{log_tail}"
    crash_markers = (
        "signal 11",
        "Remote end closed connection without response",
        "Connection refused",
        "Speculos exited with code",
    )
    if any(marker in text for marker in crash_markers):
        return "crash"
    return "error"


def run_case(
    *,
    case: Case,
    variant: str,
    elf_path: Path,
    log_root: Path,
    speculos_image: str,
    speculos_app_name: str,
    speculos_model: str,
    speculos_display: str,
    charset_mask: int,
    nickname_max_utf8_bytes: int,
) -> dict[str, Any]:
    case_log_path = log_root / f"{variant}__{case.case_id}.log"
    harness = SpeculosHarness(
        app_path=elf_path,
        speculos_image=speculos_image,
        app_name=speculos_app_name,
        model=speculos_model,
        display=speculos_display,
        apdu_port=free_port(),
        api_port=free_port(),
        log_path=case_log_path,
    )
    expected_outcome = case.expected_original if variant == "original" else case.expected_patched
    result: dict[str, Any] = {
        "variant": variant,
        "case_id": case.case_id,
        "description": case.description,
        "mode": case.mode,
        "entries": list(case.entries),
        "position": case.position,
        "expected_outcome": expected_outcome,
        "expected_selected": case.expected_selected,
        "log_path": str(case_log_path.relative_to(repo_root())),
    }

    error: Exception | None = None
    try:
        harness.start()
        harness.initialize_first_run()
        if case.mode == "push_show":
            raw = build_raw_metadatas(case.entries, charset_mask, nickname_max_utf8_bytes)
            result["raw_hex_prefix"] = raw[:64].hex()
            harness.load_metadatas(raw)
            result["screen_text"] = harness.show_password(case.position)
        elif case.mode == "ui_create_type_show":
            created = []
            for entry in case.entries:
                created.append({"nickname": entry, "screen_text": harness.create_password(entry)})
            result["created"] = created
            result["type_screen"] = harness.type_password(case.position)
            result["screen_text"] = harness.show_password(case.position)
        else:
            raise ReproError(f"Unsupported case mode: {case.mode}")
        result["selected_nickname"] = parse_selected_nickname(result["screen_text"])
    except Exception as exc:
        error = exc
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        result["screen_text"] = harness.safe_current_screen_text()
    finally:
        result["log_tail"] = harness.log_tail()
        harness.stop()

    result["actual_outcome"] = classify_outcome(error, result["log_tail"])
    selected_matches = result.get("selected_nickname") == case.expected_selected
    result["selected_matches"] = selected_matches
    result["passed"] = result["actual_outcome"] == expected_outcome and (
        expected_outcome != "ok" or selected_matches
    )
    return result


def render_markdown_report(
    *,
    run_id: str,
    build_manifest: dict[str, Any],
    lock: dict[str, Any],
    results: list[dict[str, Any]],
) -> str:
    lines = [
        "# `show second` reproduction report",
        "",
        f"- run id: `{run_id}`",
        f"- upstream repo: `{build_manifest['upstream_repo']}`",
        f"- upstream commit: `{build_manifest['upstream_commit']}`",
        f"- builder image: `{build_manifest['builder_image']}`",
        f"- speculos image: `{build_manifest['speculos_image']}`",
        "",
        "## Commands",
        "",
        "```bash",
        "./repro build",
        "./repro test",
        "```",
        "",
        "## Results",
        "",
        "| Variant | Case | Expected | Actual | Pass | Selected |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for result in results:
        selected = result.get("selected_nickname", "")
        passed = "yes" if result["passed"] else "no"
        lines.append(
            f"| `{result['variant']}` | `{result['case_id']}` | `{result['expected_outcome']}` | "
            f"`{result['actual_outcome']}` | `{passed}` | `{selected}` |"
        )
    lines.extend(
        [
            "",
            "## Details",
            "",
        ]
    )
    for result in results:
        lines.extend(
            [
                f"### `{result['variant']}` / `{result['case_id']}`",
                "",
                f"- description: {result['description']}",
                f"- expected outcome: `{result['expected_outcome']}`",
                f"- actual outcome: `{result['actual_outcome']}`",
                f"- selected nickname: `{result.get('selected_nickname', '')}`",
                f"- screen text: `{result.get('screen_text', '')}`",
                f"- log: `{result['log_path']}`",
            ]
        )
        if "error" in result:
            lines.append(f"- error: `{result['error_type']}: {result['error']}`")
        lines.append("")
    lines.extend(
        [
            "## Artifacts",
            "",
            f"- build manifest: `artifacts/build/manifest.json`",
            f"- JSON report: `artifacts/reports/run-{run_id}.json`",
            f"- Markdown report: `artifacts/reports/run-{run_id}.md`",
            "",
            "## Patch",
            "",
            "- patch file: `patches/app-passwords/0001-fix-show-second-index.patch`",
            "- patch doc: `patches/app-passwords/README.md`",
            "- root cause: `docs/root-cause.md`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    ensure_prereqs()
    root = repo_root()
    build_manifest_path = root / "artifacts" / "build" / "manifest.json"
    if not build_manifest_path.exists():
        raise ReproError("Missing build manifest. Run ./repro build first.")

    lock = load_lock()
    build_manifest = json.loads(build_manifest_path.read_text(encoding="utf-8"))
    cases = load_cases(root / "cases" / "regression_cases.json")
    run_id = utc_now_compact()
    logs_dir = ensure_dir(root / "artifacts" / "logs" / run_id)

    results: list[dict[str, Any]] = []
    for variant, elf_key in (("original", "original_elf"), ("patched", "patched_elf")):
        elf_path = Path(build_manifest[elf_key])
        for case in cases:
            print("")
            print(f"[{variant}] {case.case_id}")
            results.append(
                run_case(
                    case=case,
                    variant=variant,
                    elf_path=elf_path,
                    log_root=logs_dir,
                    speculos_image=lock["docker_images"]["speculos"],
                    speculos_app_name=lock["speculos"]["app_name"],
                    speculos_model=lock["speculos"]["model"],
                    speculos_display=lock["speculos"]["display"],
                    charset_mask=int(lock["metadata_defaults"]["charset_mask"]),
                    nickname_max_utf8_bytes=int(lock["metadata_defaults"]["nickname_max_utf8_bytes"]),
                )
            )

    report = {
        "run_id": run_id,
        "build_manifest": build_manifest,
        "lock": lock,
        "results": results,
        "failed_cases": [result for result in results if not result["passed"]],
    }

    report_json = root / "artifacts" / "reports" / f"run-{run_id}.json"
    report_md = root / "artifacts" / "reports" / f"run-{run_id}.md"
    latest_json = root / "artifacts" / "reports" / "latest.json"
    latest_md = root / "artifacts" / "reports" / "latest.md"

    write_json(report_json, report)
    write_json(latest_json, report)
    markdown = render_markdown_report(run_id=run_id, build_manifest=build_manifest, lock=lock, results=results)
    write_text(report_md, markdown + "\n")
    write_text(latest_md, markdown + "\n")

    print("")
    print(f"JSON report: {report_json}")
    print(f"Markdown report: {report_md}")

    failed = [result for result in results if not result["passed"]]
    if failed:
        print("")
        print("Failures:")
        for result in failed:
            print(
                f"- {result['variant']} / {result['case_id']}: "
                f"expected={result['expected_outcome']} actual={result['actual_outcome']}"
            )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
