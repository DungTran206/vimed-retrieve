"""CLI nhẹ, lazy imports; job mặc định dry-run, lỗi có JSON code."""
from __future__ import annotations
import argparse
import json
import os
import sys
from .contracts import BearError, InputMissingError, SchemaInvalidError, RUNTIME_DIR
from .config import command_config
from .io import canonical_json_dumps, resolve_repo_path


def runtime_environment():
    paths = {"TEMP": "tmp", "TMP": "tmp", "TMPDIR": "tmp", "HF_HOME": "cache/huggingface",
             "HF_HUB_CACHE": "cache/huggingface/hub", "TORCH_HOME": "cache/torch",
             "SENTENCE_TRANSFORMERS_HOME": "cache/sentence_transformers",
             "XDG_CACHE_HOME": "cache", "PIP_CACHE_DIR": "cache/pip", "UV_CACHE_DIR": "cache/uv"}
    for key, suffix in paths.items():
        os.environ[key] = str(RUNTIME_DIR / suffix)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True
    (RUNTIME_DIR / "tmp").mkdir(parents=True, exist_ok=True)


def dry_run(cfg, command):
    from .artifacts import required_path
    from .io import assert_valid_output_path
    if cfg.get("output_dir"):
        assert_valid_output_path(resolve_repo_path(cfg["output_dir"]))
    if command in ("reproduce", "export"):
        from .reproduce import preflight
        return preflight(cfg)
    paths = {"pool": ("baseline", "deeper", "corpus", "membership"),
             "features": ("pool_manifest", "queries", "corpus"),
             "run": ("pool_manifest",), "sample": ("queries", "protocol"),
             "annotation-export": ("queries", "corpus", "baseline", "split_manifest")}
    missing = []
    keys = list(paths.get(command, ()))
    if command == "run" and cfg["mode"] != "baseline" and cfg.get("lambda", 0) != 0:
        keys.append("feature_manifest")
    for key in keys:
        try:
            required_path(cfg.get(key))
        except InputMissingError:
            missing.append(key)
    return {"status": "blocked_input" if missing else "inputs_present_unverified",
            "missing_roles": missing, "command": command, "dry_run": True,
            "output_dir": cfg.get("output_dir")}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -B -m TXT.bear.cli", description="BEAR CPU workflow")
    subs = parser.add_subparsers(dest="command")
    for name in ("audit", "reproduce", "pool", "features", "run", "sample", "annotation-export", "export"):
        sub = subs.add_parser(name)
        sub.add_argument("--config", required=True)
        if name != "audit":
            group = sub.add_mutually_exclusive_group()
            group.add_argument("--dry-run", action="store_true")
            group.add_argument("--execute", action="store_true")
        if name == "reproduce":
            sub.add_argument("--export", action="store_true")
        if name == "export":
            sub.add_argument("--run-dir", required=True)
    for name in ("evaluate", "compare"):
        sub = subs.add_parser(name)
        sub.add_argument("--config", required=True)
        if name == "evaluate":
            sub.add_argument("--run-dir", required=True)
        else:
            sub.add_argument("--baseline-dir", required=True)
            sub.add_argument("--candidate-dir", required=True)
    sub = subs.add_parser("freeze")
    sub.add_argument("--run-dir", required=True)
    sub.add_argument("--protocol", required=True)
    sub = subs.add_parser("tune")
    sub.add_argument("--protocol", required=True)
    sub.add_argument("--menu", required=True)
    sub.add_argument("--split", choices=("dev",), default="dev")
    group = sub.add_mutually_exclusive_group()
    group.add_argument("--execute", action="store_true")
    group.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        runtime_environment()
        if args.command == "tune":
            from .tuning import tune
            result = tune(args.protocol, args.menu, args.split, args.execute)
        elif args.command == "freeze":
            from .experiments import freeze
            result = freeze(args.run_dir, args.protocol)
        else:
            command = "evaluate" if args.command == "compare" else args.command
            cfg = command_config(args.config, command)
            if command == "audit":
                from .audit import run_audit
                result, code = run_audit(args.config)
                print(canonical_json_dumps({"status": result["readiness_status"],
                                           "missing_roles": result["missing_roles"],
                                           "invalid_roles": result["invalid_roles"]}))
                return code
            elif command == "evaluate":
                from .evaluate_runner import evaluate
                result = evaluate(cfg, args.candidate_dir if args.command == "compare" else args.run_dir,
                                  args.baseline_dir if args.command == "compare" else None)
            elif not args.execute:
                result = dry_run(cfg, command)
            elif command == "reproduce":
                from .reproduce import execute
                result = execute(cfg, export=args.export)
            elif command in ("pool", "features", "run"):
                from .features import create_pools, compute_features, inference
                result = {"pool": create_pools, "features": compute_features, "run": inference}[command](cfg)
            elif command in ("sample", "annotation-export"):
                from .experiments import sample, annotation_export
                result = (sample if command == "sample" else annotation_export)(cfg)
            elif command == "export":
                from .release import export_run
                result = export_run(cfg, args.run_dir)
        print(canonical_json_dumps(result))
        return 1 if result.get("status") in ("blocked_input", "inconclusive") else 0
    except (FileNotFoundError, KeyError) as error:
        diagnostic = {"code": "INPUT_MISSING" if isinstance(error, FileNotFoundError) else "SCHEMA_INVALID", "message": str(error)}
    except BearError as error:
        diagnostic = {"code": error.code, "message": error.message, "details": error.details}
    except (TypeError, ValueError) as error:
        diagnostic = {"code": "SCHEMA_INVALID", "message": str(error)}
    print(canonical_json_dumps(diagnostic), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
