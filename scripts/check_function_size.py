#!/usr/bin/env python3
"""Check directory size and fail with a clear message if it exceeds threshold.

Usage:
  python scripts/check_function_size.py -p <path> -t <threshold_mb>

This prints a human-friendly summary and exits with code 2 when the threshold is exceeded.
It also prints the top N largest directories to help identify the offenders.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from collections import defaultdict


def human_readable(num_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} TB"


def get_sizes(base_path: Path, exclude: set[str]) -> tuple[int, dict[str, int]]:
    total = 0
    dir_sizes: dict[str, int] = defaultdict(int)
    for root, dirs, files in os.walk(base_path, topdown=True):
        # filter out excluded directories in-place for speed
        dirs[:] = [d for d in dirs if d not in exclude]
        for f in files:
            try:
                fp = os.path.join(root, f)
                size = os.path.getsize(fp)
                total += size
                dir_sizes[root] += size
            except OSError:
                # Skip files we can't access
                continue
    return total, dir_sizes


def print_top(dir_sizes: dict[str, int], top_n: int = 10) -> None:
    items = sorted(dir_sizes.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    if not items:
        return

    print("\nTop offenders (path — size):")
    for path, size in items:
        print(f"  {path} — {human_readable(size)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fail if a directory's size exceeds a threshold (MB).")
    parser.add_argument("-p", "--path", default=".", help="Path to measure (default: project root)" )
    parser.add_argument("-t", "--threshold", type=float, default=250.0, help="Threshold in MB (default: 250)")
    parser.add_argument("--top", type=int, default=10, help="Show top N largest directories")
    parser.add_argument("--exclude", type=str, nargs="*", default=[".git", "node_modules", "venv", ".venv", "__pycache__"],
                        help="Directories to exclude from the size calculation")

    args = parser.parse_args()

    base = Path(args.path).resolve()
    if not base.exists():
        print(f"ERROR: path does not exist: {base}")
        sys.exit(2)

    exclude = set(args.exclude)
    print(f"Checking size of: {base}")
    print(f"Excluding: {', '.join(sorted(exclude))}")
    print(f"Threshold: {args.threshold} MB")

    total_bytes, dir_sizes = get_sizes(base, exclude)
    total_mb = total_bytes / (1024.0 * 1024.0)

    print(f"Detected uncompressed size: {total_mb:.2f} MB")

    if total_mb > args.threshold:
        print("\nERROR: Detected uncompressed size exceeds the Vercel serverless function limit (250 MB).", file=sys.stderr)
        print("See: https://vercel.link/serverless-function-size", file=sys.stderr)
        print_top(dir_sizes, top_n=args.top)
        # Exit with a non-zero code so this can be used in CI/predeploy hooks
        sys.exit(2)

    # Otherwise succeed with 0
    sys.exit(0)


if __name__ == '__main__':
    main()
