#!/usr/bin/env python3
"""Fetch the pinned ST SDK into a private-to-build, ignored directory."""
import argparse
from pathlib import Path
import subprocess
REVISION = "abeee83eb7181ce278c65681196ede45c930a7ec"
SUBMODULES = ["arch/cmsis", "stm32c5xx_dfp", "stm32c5xx_drivers"]
def run(*args):
    subprocess.run(args, check=True)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, default=Path(__file__).resolve().parents[1]/".deps/STM32CubeC5")
    args = parser.parse_args()
    dest = args.destination.resolve()
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        run("git", "clone", "--depth", "1", "--branch", "2.1.0", "--filter=blob:none", "--sparse", "https://github.com/STMicroelectronics/STM32CubeC5.git", str(dest))
    revision = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
    if revision != REVISION:
        raise SystemExit("Unexpected SDK revision; refusing to overwrite checkout")
    run("git", "-C", str(dest), "sparse-checkout", "set", "--skip-checks", "examples/hal/uart/echo_polling/NUCLEO-C5A3ZG", *SUBMODULES)
    run("git", "-C", str(dest), "submodule", "update", "--init", "--depth", "1", *SUBMODULES)
    print(dest)
if __name__ == "__main__":
    main()
