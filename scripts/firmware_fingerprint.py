#!/usr/bin/env python3
"""Print a deterministic 12-hex fingerprint of all firmware-producing inputs."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

STATIC_INPUTS = (Path("Dockerfile"), Path("bin/build.sh"))


def input_paths(root: Path) -> list[Path]:
    paths = [root / relative for relative in STATIC_INPUTS]
    config = root / "config"
    if not config.is_dir():
        raise FileNotFoundError(f"missing firmware config directory: {config}")
    paths.extend(path for path in config.rglob("*") if path.is_file() and path.name != ".DS_Store")
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing firmware inputs: " + ", ".join(str(path) for path in missing))
    return sorted(paths, key=lambda path: path.relative_to(root).as_posix())


def fingerprint(root: Path) -> str:
    root = root.resolve()
    digest = hashlib.sha256()
    for path in input_paths(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()[:12]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        print(fingerprint(args.root))
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
