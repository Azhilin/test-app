"""
Smoke-test project_setup.bat without performing a full install.

Usage:
    python tools/smoke_test_setup.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SETUP_SCRIPT = REPO_ROOT / "project_setup.bat"
ENV_TEMPLATE = REPO_ROOT / ".env.example"


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n")


def _prepare_workspace(workdir: Path, *, include_template: bool = True) -> None:
    shutil.copy2(SETUP_SCRIPT, workdir / SETUP_SCRIPT.name)
    if include_template:
        shutil.copy2(ENV_TEMPLATE, workdir / ENV_TEMPLATE.name)


def _run_setup(
    workdir: Path,
    *,
    user_input: str = "",
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    args = ["cmd", "/c", str(workdir / SETUP_SCRIPT.name), "--smoke-test"]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(
        args,
        cwd=workdir,
        input=user_input,
        capture_output=True,
        text=True,
        check=False,
    )


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _get_log_file(workdir: Path) -> Path:
    log_files = sorted((workdir / "generated" / "logs").glob("project_setup-*.log"))
    _assert(len(log_files) == 1, f"expected one generated log file, found {len(log_files)}")
    return log_files[0]


def test_creates_env_when_missing() -> None:
    with tempfile.TemporaryDirectory(prefix="setup-smoke-") as tmp:
        workdir = Path(tmp)
        _prepare_workspace(workdir)

        result = _run_setup(workdir)
        output = _normalize(result.stdout + result.stderr)
        log_file = _get_log_file(workdir)
        log_output = _normalize(log_file.read_text(encoding="utf-8"))
        env_path = str(workdir / ".env")
        env_template_path = str(workdir / ".env.example")

        _assert(result.returncode == 0, f"expected success, got {result.returncode}\n{output}")
        _assert((workdir / ".env").exists(), ".env was not created")
        _assert(
            _normalize((workdir / ".env").read_text(encoding="utf-8"))
            == _normalize((workdir / ".env.example").read_text(encoding="utf-8")),
            ".env content does not match .env.example",
        )
        _assert("generated/logs" in str(log_file).replace("\\", "/"), "log file should be written under generated/logs")
        _assert("Writing setup log to" in output, "log path message missing")
        _assert(
            f"Created '.env' at '{env_path}' from '{env_template_path}' with default values." in output,
            "create message with exact paths missing from console output",
        )
        _assert(
            f"Created '.env' at '{env_path}' from '{env_template_path}' with default values." in log_output,
            "create message with exact paths missing from log file",
        )


def test_keeps_existing_env_by_default() -> None:
    with tempfile.TemporaryDirectory(prefix="setup-smoke-") as tmp:
        workdir = Path(tmp)
        _prepare_workspace(workdir)
        original = "JIRA_URL=https://keep.example\n"
        (workdir / ".env").write_text(original, encoding="utf-8")

        result = _run_setup(workdir, user_input="\n")
        output = _normalize(result.stdout + result.stderr)
        log_file = _get_log_file(workdir)
        log_output = _normalize(log_file.read_text(encoding="utf-8"))
        env_path = str(workdir / ".env")

        _assert(result.returncode == 0, f"expected success, got {result.returncode}\n{output}")
        _assert((workdir / ".env").read_text(encoding="utf-8") == original, ".env should remain unchanged")
        _assert("Leaving it unchanged" in output, "keep message missing")
        _assert(
            f"Existing '.env' found at '{env_path}'. Leaving it unchanged." in log_output,
            "exact keep-path message missing from log file",
        )


def test_backs_up_and_recreates_existing_env() -> None:
    with tempfile.TemporaryDirectory(prefix="setup-smoke-") as tmp:
        workdir = Path(tmp)
        _prepare_workspace(workdir)
        original = "JIRA_URL=https://backup.example\n"
        (workdir / ".env").write_text(original, encoding="utf-8")

        result = _run_setup(workdir, user_input="B\n")
        output = _normalize(result.stdout + result.stderr)
        log_file = _get_log_file(workdir)
        log_output = _normalize(log_file.read_text(encoding="utf-8"))
        env_path = str(workdir / ".env")
        env_template_path = str(workdir / ".env.example")

        backups = sorted(workdir.glob(".env.backup-*"))
        _assert(result.returncode == 0, f"expected success, got {result.returncode}\n{output}")
        _assert(len(backups) == 1, f"expected one backup file, found {len(backups)}")
        _assert(backups[0].read_text(encoding="utf-8") == original, "backup file content is incorrect")
        _assert(
            _normalize((workdir / ".env").read_text(encoding="utf-8"))
            == _normalize((workdir / ".env.example").read_text(encoding="utf-8")),
            ".env should be recreated from the template",
        )
        _assert(f"Backed up '{env_path}' to '{backups[0]}'." in log_output, "backup path message missing")
        _assert(
            f"Recreated '.env' at '{env_path}' from '{env_template_path}' with default values." in log_output,
            "recreate path message missing",
        )


def test_invalid_choice_defaults_to_keep() -> None:
    with tempfile.TemporaryDirectory(prefix="setup-smoke-") as tmp:
        workdir = Path(tmp)
        _prepare_workspace(workdir)
        original = "JIRA_URL=https://invalid.example\n"
        (workdir / ".env").write_text(original, encoding="utf-8")

        result = _run_setup(workdir, user_input="X\n")
        output = _normalize(result.stdout + result.stderr)

        _assert(result.returncode == 0, f"expected success, got {result.returncode}\n{output}")
        _assert((workdir / ".env").read_text(encoding="utf-8") == original, ".env should remain unchanged")
        _assert("Unrecognized choice 'X'" in output, "invalid-choice message missing")


def test_missing_template_warns_and_skips_creation() -> None:
    with tempfile.TemporaryDirectory(prefix="setup-smoke-") as tmp:
        workdir = Path(tmp)
        _prepare_workspace(workdir, include_template=False)

        result = _run_setup(workdir)
        output = _normalize(result.stdout + result.stderr)
        log_file = _get_log_file(workdir)
        log_output = _normalize(log_file.read_text(encoding="utf-8"))
        env_path = str(workdir / ".env")
        env_template_path = str(workdir / ".env.example")

        _assert(result.returncode == 0, f"expected success, got {result.returncode}\n{output}")
        _assert(not (workdir / ".env").exists(), ".env should not be created without a template")
        _assert("'%.env.example%' not found" not in output, "unexpected malformed placeholder in output")
        _assert(
            f"'.env.example' not found at '{env_template_path}'. Skipping '.env' creation at '{env_path}'." in log_output,
            "missing-template warning with exact paths absent",
        )


def test_keep_flag_skips_prompt_and_preserves_env() -> None:
    with tempfile.TemporaryDirectory(prefix="setup-smoke-") as tmp:
        workdir = Path(tmp)
        _prepare_workspace(workdir)
        original = "JIRA_URL=https://flag-keep.example\n"
        (workdir / ".env").write_text(original, encoding="utf-8")

        result = _run_setup(workdir, extra_args=["--keep-env"])
        output = _normalize(result.stdout + result.stderr)

        _assert(result.returncode == 0, f"expected success, got {result.returncode}\n{output}")
        _assert((workdir / ".env").read_text(encoding="utf-8") == original, ".env should remain unchanged")
        _assert("--keep-env was provided" in output, "keep-flag message missing")
        _assert("Choose [K/B]" not in output, "interactive prompt should be skipped")


def test_refresh_flag_backs_up_and_recreates_env() -> None:
    with tempfile.TemporaryDirectory(prefix="setup-smoke-") as tmp:
        workdir = Path(tmp)
        _prepare_workspace(workdir)
        original = "JIRA_URL=https://flag-refresh.example\n"
        (workdir / ".env").write_text(original, encoding="utf-8")

        result = _run_setup(workdir, extra_args=["--refresh-env"])
        output = _normalize(result.stdout + result.stderr)
        backups = sorted(workdir.glob(".env.backup-*"))

        _assert(result.returncode == 0, f"expected success, got {result.returncode}\n{output}")
        _assert(len(backups) == 1, f"expected one backup file, found {len(backups)}")
        _assert(backups[0].read_text(encoding="utf-8") == original, "backup content is incorrect")
        _assert(
            _normalize((workdir / ".env").read_text(encoding="utf-8"))
            == _normalize((workdir / ".env.example").read_text(encoding="utf-8")),
            ".env should be recreated from the template",
        )
        _assert("--refresh-env was provided" in output, "refresh-flag message missing")
        _assert("Choose [K/B]" not in output, "interactive prompt should be skipped")


def test_conflicting_env_flags_fail_fast() -> None:
    with tempfile.TemporaryDirectory(prefix="setup-smoke-") as tmp:
        workdir = Path(tmp)
        _prepare_workspace(workdir)

        result = _run_setup(workdir, extra_args=["--keep-env", "--refresh-env"])
        output = _normalize(result.stdout + result.stderr)

        _assert(result.returncode != 0, "conflicting flags should fail")
        _assert("Conflicting .env options" in output, "conflict message missing")


def main() -> int:
    if os.name != "nt":
        print("This smoke test must be run on Windows because it executes a .bat file.", file=sys.stderr)
        return 1

    if not SETUP_SCRIPT.is_file():
        print(f"Missing setup script: {SETUP_SCRIPT}", file=sys.stderr)
        return 1

    if not ENV_TEMPLATE.is_file():
        print(f"Missing env template: {ENV_TEMPLATE}", file=sys.stderr)
        return 1

    tests = [
        ("create env from template", test_creates_env_when_missing),
        ("keep existing env by default", test_keeps_existing_env_by_default),
        ("backup and recreate env", test_backs_up_and_recreates_existing_env),
        ("invalid choice defaults keep", test_invalid_choice_defaults_to_keep),
        ("missing template warns", test_missing_template_warns_and_skips_creation),
        ("keep flag skips prompt", test_keep_flag_skips_prompt_and_preserves_env),
        ("refresh flag recreates env", test_refresh_flag_backs_up_and_recreates_env),
        ("conflicting flags fail fast", test_conflicting_env_flags_fail_fast),
    ]

    for name, test_func in tests:
        try:
            test_func()
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {name}: {exc}", file=sys.stderr)
            return 1
        print(f"[PASS] {name}")

    print("Smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
