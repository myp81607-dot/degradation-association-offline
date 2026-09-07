"""Command-line entry point for one-shot offline degradation analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .input import OfflineInputError
from .offline import OfflineAnalysisError, analyze_offline
from .state import StateError
from .window import WindowError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m experiment.degradation.cli",
        description="Analyze saved Prometheus matrix data in one batch.",
    )
    parser.add_argument("command", choices=("analyze",))
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Prometheus matrix JSON/TXT files or directories containing them.",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path("outputs/degradation-association-offline"),
    )
    parser.add_argument(
        "--baseline-file",
        type=Path,
        help="Load this baseline, or create it from the first 30 complete steps.",
    )
    parser.add_argument("--output", type=Path, help="Result JSON path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    state_dir = args.state_dir.expanduser()
    baseline = (
        args.baseline_file.expanduser()
        if args.baseline_file is not None
        else state_dir / "standard_data.json"
    )
    output = (
        args.output.expanduser()
        if args.output is not None
        else state_dir / "abnormal_data.json"
    )
    try:
        result = analyze_offline(
            args.inputs, baseline_path=baseline, output_path=output
        )
    except (
        OfflineAnalysisError,
        OfflineInputError,
        StateError,
        WindowError,
        TypeError,
        ValueError,
    ) as exc:
        error_kind = (
            "offline_analysis_error"
            if isinstance(exc, OfflineAnalysisError)
            else "invalid_input_or_state"
        )
        print(
            json.dumps(
                {"status": "error", "error_kind": error_kind, "message": str(exc)},
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
