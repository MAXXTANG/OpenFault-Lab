#!/usr/bin/env python3
"""Run a local synthetic demonstration or evaluate controlled WAV sessions (MIT)."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"host"))
from openfault.pipeline import evaluate, make_demo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("demo", "evaluate"):
        command = commands.add_parser(name)
        command.add_argument("--out", type=Path, required=True, help="A new output directory; never overwrites")
        command.add_argument("--extractor", type=Path, default=ROOT/"build/host/pcm_features")
        if name == "evaluate":
            command.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "demo":
            args.out.mkdir(parents=True, exist_ok=False)
            manifest = make_demo(args.out/"synthetic_inputs")
            result = evaluate(manifest, args.extractor, args.out/"evaluation")
            report = args.out/"evaluation/report.html"
        else:
            result = evaluate(args.manifest, args.extractor, args.out)
            report = args.out/"report.html"
        print(json.dumps({"provenance": result["provenance"], "metrics": result["metrics"], "report": str(report.resolve())}, indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"Offline evaluation failed: {error}\n")
if __name__ == "__main__":
    main()
