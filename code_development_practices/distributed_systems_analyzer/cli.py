"""Command-line interface for repository analysis."""

import argparse
import json
import sys

from .analyzer import analyze_repository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ds-analyze",
        description="Score a repository's distributed-systems architectural readiness.",
    )
    parser.add_argument("repository", help="Path to the application repository")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Report output format (default: text)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        report = analyze_repository(args.repository)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.render_text())
    return 0

