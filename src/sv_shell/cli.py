# SPDX-FileCopyrightText: 2026 sv-shell contributors
# SPDX-License-Identifier: LGPL-3.0-or-later

from __future__ import annotations

import argparse
import sys

from .generator import ShellGenerationError, shell_from_sv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sv-shell",
        description=(
            "Generate an empty SystemVerilog shell with all signal types forced to logic "
            "using py-slang AST parsing."
        ),
    )
    parser.add_argument("input", help="Path to a single Verilog/SystemVerilog source file")
    parser.add_argument(
        "-o",
        "--output",
        help="Write generated shell to this file (defaults to stdout)",
    )
    parser.add_argument(
        "-m",
        "--module",
        help="Generate shell only for a specific module name",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        output = shell_from_sv(args.input, module_name=args.module)
    except (OSError, ShellGenerationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(output)
    else:
        print(output, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
