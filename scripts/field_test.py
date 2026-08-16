#!/usr/bin/env python3
"""Record and enforce the seven-day Advantage360 physical field test."""

from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

FIELDS = [
    "timestamp",
    "os",
    "minutes",
    "thumb_misfires",
    "layer_errors",
    "home_row_misfires",
    "combo_misfires",
    "aggressive_input_measured",
    "shortcut_mismatches",
    "macro_output_errors",
    "macro_output_measured",
    "awkward_symbols",
    "planned_corrections",
    "notes",
]
PRE_AGGRESSIVE_FIELDS = [
    "timestamp", "os", "minutes", "thumb_misfires", "layer_errors",
    "shortcut_mismatches", "macro_output_errors", "macro_output_measured",
    "awkward_symbols", "planned_corrections", "notes",
]
PREVIOUS_FIELDS = [field for field in PRE_AGGRESSIVE_FIELDS if field != "macro_output_measured"]
PRE_MACRO_FIELDS = [field for field in PREVIOUS_FIELDS if field != "macro_output_errors"]
LEGACY_FIELDS = [field for field in PRE_MACRO_FIELDS if field != "planned_corrections"]
INTEGER_FIELDS = (
    "minutes", "thumb_misfires", "layer_errors", "home_row_misfires",
    "combo_misfires", "shortcut_mismatches", "macro_output_errors",
)
MIN_SESSION_MINUTES = 30
MIN_TOTAL_MINUTES = 420
MIN_OS_MINUTES = 60
AWKWARD_REPEAT_THRESHOLD = 3


class LogError(ValueError):
    """A field-test CSV is malformed or semantically invalid."""


def default_log() -> Path:
    override = os.environ.get("ADV360_FIELD_LOG")
    return Path(override).expanduser() if override else Path.home() / ".local/state/adv360-field-test.csv"


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = (path.stat().st_mode & 0o7777) if path.exists() else 0o600
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def backup_before_migration(path: Path) -> Path:
    """Create a durable backup without overwriting or reusing stale content."""
    base = path.with_name(path.name + ".pre-migration.bak")
    data = path.read_bytes()
    mode = path.stat().st_mode & 0o7777
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{base.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())

        index = 0
        while True:
            backup = base if index == 0 else base.with_name(f"{base.name}.{index}")
            try:
                os.link(temporary, backup)
                break
            except FileExistsError:
                index += 1
        sync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)
    return backup


def validate_row(row: dict[str, str], line_number: int) -> dict[str, str]:
    missing = [field for field in FIELDS if field not in row or row[field] is None]
    if missing:
        raise LogError(f"line {line_number}: missing fields: {', '.join(missing)}")
    try:
        datetime.fromisoformat(row["timestamp"])
    except ValueError as error:
        raise LogError(f"line {line_number}: invalid timestamp {row['timestamp']!r}") from error
    if row["os"] not in {"macos", "linux"}:
        raise LogError(f"line {line_number}: os must be macos or linux, got {row['os']!r}")
    for field in INTEGER_FIELDS:
        try:
            value = int(row[field])
        except ValueError as error:
            raise LogError(f"line {line_number}: {field} must be an integer, got {row[field]!r}") from error
        if value < 0:
            raise LogError(f"line {line_number}: {field} must be non-negative")
        row[field] = str(value)
    if int(row["minutes"]) == 0:
        raise LogError(f"line {line_number}: minutes must be greater than zero")
    for field in ("macro_output_measured", "aggressive_input_measured"):
        if row[field] not in {"yes", "no"}:
            raise LogError(f"line {line_number}: {field} must be yes or no")
    return row


def read_rows(path: Path, migrate: bool = False) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        if fieldnames not in (FIELDS, PRE_AGGRESSIVE_FIELDS, PREVIOUS_FIELDS, PRE_MACRO_FIELDS, LEGACY_FIELDS):
            raise LogError(f"invalid CSV header in {path}: expected {FIELDS}, got {fieldnames}")
        rows = list(reader)

    if fieldnames != FIELDS:
        for row in rows:
            row["home_row_misfires"] = "0"
            row["combo_misfires"] = "0"
            row["aggressive_input_measured"] = "no"
    if fieldnames == PREVIOUS_FIELDS:
        for row in rows:
            row["macro_output_measured"] = "yes"
    if fieldnames in (PRE_MACRO_FIELDS, LEGACY_FIELDS):
        for row in rows:
            row["macro_output_errors"] = "0"
            row["macro_output_measured"] = "no"
    if fieldnames == LEGACY_FIELDS:
        for row in rows:
            row["planned_corrections"] = ""
    validated = [validate_row(dict(row), line_number) for line_number, row in enumerate(rows, start=2)]
    if fieldnames != FIELDS and migrate:
        backup_before_migration(path)
        write_rows(path, validated)

    return validated


def ensure_log(path: Path) -> None:
    if not path.exists():
        write_rows(path, [])
    else:
        read_rows(path, migrate=True)


def command_init(args: argparse.Namespace) -> int:
    ensure_log(args.log)
    print(args.log)
    return 0


def command_log(args: argparse.Namespace) -> int:
    ensure_log(args.log)
    if args.minutes < MIN_SESSION_MINUTES:
        raise LogError(f"a qualifying session must be at least {MIN_SESSION_MINUTES} minutes")
    row = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "os": args.os,
        "minutes": str(args.minutes),
        "thumb_misfires": str(args.thumb_misfires),
        "layer_errors": str(args.layer_errors),
        "home_row_misfires": str(args.home_row_misfires),
        "combo_misfires": str(args.combo_misfires),
        "aggressive_input_measured": "yes",
        "shortcut_mismatches": str(args.shortcut_mismatches),
        "macro_output_errors": str(args.macro_output_errors),
        "macro_output_measured": "yes",
        "awkward_symbols": args.awkward_symbols,
        "planned_corrections": args.planned_corrections,
        "notes": args.notes,
    }
    validate_row(row, 2)
    with args.log.open("a", newline="") as handle:
        csv.DictWriter(handle, fieldnames=FIELDS).writerow(row)
    print(f"recorded {args.minutes} minutes on {args.os}: {args.log}")
    return 0


def command_report(args: argparse.Namespace) -> int:
    rows = read_rows(args.log)
    if not rows:
        print(f"no observations: {args.log}")
        return 1 if args.strict else 0

    totals: defaultdict[str, int] = defaultdict(int)
    operating_systems: Counter[str] = Counter()
    day_minutes: Counter[str] = Counter()
    awkward: Counter[str] = Counter()
    planned: set[str] = set()
    for row in rows:
        day = row["timestamp"][:10]
        minutes = int(row["minutes"])
        day_minutes[day] += minutes
        operating_systems[row["os"]] += minutes
        for name in INTEGER_FIELDS:
            totals[name] += int(row[name])
        awkward.update(token for token in row["awkward_symbols"].split() if token)
        planned.update(token for token in row["planned_corrections"].split() if token)

    hours = totals["minutes"] / 60
    thumb_rate = totals["thumb_misfires"] / hours if hours else float("inf")
    layer_rate = totals["layer_errors"] / hours if hours else float("inf")
    home_row_rate = totals["home_row_misfires"] / hours if hours else float("inf")
    combo_rate = totals["combo_misfires"] / hours if hours else float("inf")
    recurring = {symbol for symbol, count in awkward.items() if count >= AWKWARD_REPEAT_THRESHOLD}
    recurring_unplanned = sorted(recurring - planned)

    checks = {
        "seven distinct days": len(day_minutes) >= 7,
        f"every day >= {MIN_SESSION_MINUTES} minutes": bool(day_minutes) and all(minutes >= MIN_SESSION_MINUTES for minutes in day_minutes.values()),
        f"total time >= {MIN_TOTAL_MINUTES} minutes": totals["minutes"] >= MIN_TOTAL_MINUTES,
        f"macOS and Linux each >= {MIN_OS_MINUTES} minutes": all(operating_systems[name] >= MIN_OS_MINUTES for name in ("macos", "linux")),
        "thumb misfires <= 0.5/hour": thumb_rate <= 0.5,
        "layer errors <= 0.5/hour": layer_rate <= 0.5,
        "home-row mod misfires <= 0.5/hour": home_row_rate <= 0.5,
        "zero combo misfires": totals["combo_misfires"] == 0,
        "aggressive input measured in every session": all(row["aggressive_input_measured"] == "yes" for row in rows),
        "zero shortcut mismatches": totals["shortcut_mismatches"] == 0,
        "macro output measured in every session": all(row["macro_output_measured"] == "yes" for row in rows),
        "zero macro output errors": totals["macro_output_errors"] == 0,
        f"no unplanned symbol reported >= {AWKWARD_REPEAT_THRESHOLD} times": not recurring_unplanned,
    }

    print(f"log: {args.log}")
    print(f"sessions={len(rows)} days={len(day_minutes)} minutes={totals['minutes']}")
    print("OS minutes: " + ", ".join(f"{name}={minutes}" for name, minutes in sorted(operating_systems.items())))
    print(f"thumb_misfires/hour={thumb_rate:.2f} layer_errors/hour={layer_rate:.2f} "
          f"home_row_misfires/hour={home_row_rate:.2f} combo_misfires/hour={combo_rate:.2f}")
    print(f"shortcut_mismatches={totals['shortcut_mismatches']} macro_output_errors={totals['macro_output_errors']}")
    if awkward:
        print("awkward symbols: " + ", ".join(f"{symbol}={count}" for symbol, count in awkward.most_common()))
    if planned:
        print("planned corrections: " + " ".join(sorted(planned)))
    if recurring_unplanned:
        print("unplanned recurring symbols: " + " ".join(recurring_unplanned))
    for label, passed in checks.items():
        print(f"{'PASS' if passed else 'PENDING'}: {label}")

    passed = all(checks.values())
    print("FIELD TEST PASS" if passed else "FIELD TEST INCOMPLETE")
    return 0 if passed or not args.strict else 1


def add_log_option(parser: argparse.ArgumentParser, *, root: bool = False) -> None:
    default = default_log() if root else argparse.SUPPRESS
    parser.add_argument("--log", type=Path, default=default, help="CSV log path (also ADV360_FIELD_LOG)")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    add_log_option(root, root=True)
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="create or migrate the field-test log")
    add_log_option(init)
    init.set_defaults(func=command_init)

    log = commands.add_parser("log", help=f"record a physical session of at least {MIN_SESSION_MINUTES} minutes")
    add_log_option(log)
    log.add_argument("--os", choices=("macos", "linux"), required=True)
    log.add_argument("--minutes", type=int, required=True)
    log.add_argument("--thumb-misfires", type=int, default=0)
    log.add_argument("--layer-errors", type=int, default=0)
    log.add_argument("--home-row-misfires", type=int, default=0, help="letter/modifier decisions that resolved incorrectly")
    log.add_argument("--combo-misfires", type=int, default=0, help="missed or unintended home-row combo activations")
    log.add_argument("--shortcut-mismatches", type=int, default=0)
    log.add_argument("--macro-output-errors", type=int, default=0, help="dropped, duplicated, or reordered firmware-macro characters")
    log.add_argument("--awkward-symbols", default="", help="space-separated symbols that felt awkward")
    log.add_argument("--planned-corrections", default="", help="space-separated awkward symbols with an explicit remap plan")
    log.add_argument("--notes", default="")
    log.set_defaults(func=command_log)

    report = commands.add_parser("report", help="summarize progress and evaluate acceptance thresholds")
    add_log_option(report)
    report.add_argument("--strict", action="store_true", help="exit nonzero until every acceptance gate passes")
    report.set_defaults(func=command_report)
    return root


def main() -> int:
    args = parser().parse_args()
    for name in INTEGER_FIELDS:
        if hasattr(args, name) and getattr(args, name) < 0:
            raise SystemExit(f"{name} must be non-negative")
    try:
        return args.func(args)
    except LogError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
