#!/usr/bin/env python3
"""Build the synthetic STM32 target; never flash a device."""
import argparse
import os
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk", type=Path, default=ROOT/".deps/STM32CubeC5")
    parser.add_argument("--toolchain-bin", type=Path, default=ROOT/".tools/arm-gnu-toolchain-14.3.rel1/bin")
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()
    env = os.environ.copy()
    if args.toolchain_bin.is_dir():
        env["PATH"] = str(args.toolchain_bin.resolve())+os.pathsep+env.get("PATH", "")
    command = ["cmake", "-S", str(ROOT/"firmware/stm32c5"), "-B", str(ROOT/"build/stm32c5"), "-G", "Ninja", "-DCMAKE_TOOLCHAIN_FILE="+str(ROOT/"firmware/stm32c5/arm-gcc.cmake"), "-DST_CUBE_ROOT="+str(args.sdk.resolve())]
    if args.fresh:
        command.append("--fresh")
    subprocess.run(command, env=env, check=True)
    subprocess.run(["cmake", "--build", str(ROOT/"build/stm32c5")], env=env, check=True)
if __name__ == "__main__":
    main()
