"""Executable experiment entry point; offline demo needs only Python stdlib."""
from __future__ import annotations

import argparse
import sys

from .contracts import BearError
from .io import canonical_json_dumps, load_config


def main(argv=None):
    parser = argparse.ArgumentParser(description="Medical keyword gate hypothesis, not a promoted production recipe")
    subparsers = parser.add_subparsers(dest="command")
    for command in ("kb-import", "prepare", "document-terms", "cache", "fit", "tune", "run", "evaluate"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--config", required=True)
        mode = sub.add_mutually_exclusive_group()
        mode.add_argument("--execute", action="store_true")
        mode.add_argument("--dry-run", action="store_true")
    demo = subparsers.add_parser("demo")
    demo.add_argument("--output-dir", default="TXT/runtime/medical_hypothesis_demo")
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    try:
        from .cli import runtime_environment
        runtime_environment()
        if args.command == "demo":
            from TXT.tools.demo_medical_hypothesis import run_demo
            result = run_demo(args.output_dir)
        else:
            from .medical_runner import inspect_experiment, run_experiment
            config = load_config(args.config)
            result = run_experiment(args.command, config) if args.execute else inspect_experiment(args.command, config)
        print(canonical_json_dumps(result))
        return 1 if result.get("status") == "blocked_input" else 0
    except BearError as error:
        print(canonical_json_dumps({"code": error.code, "message": error.message, "details": error.details}), file=sys.stderr)
    except (ValueError, TypeError, KeyError, FileNotFoundError, OSError) as error:
        print(canonical_json_dumps({"code": "INPUT_MISSING" if isinstance(error, FileNotFoundError) else "EXPERIMENT_ERROR", "message": str(error)}), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
