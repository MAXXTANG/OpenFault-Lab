#!/usr/bin/env python3
"""Stage the shared original C files, then build (never upload) the XIAO sketch."""
import argparse
from pathlib import Path
import shutil
import subprocess
ROOT = Path(__file__).resolve().parents[1]
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file", type=Path)
    parser.add_argument("--fqbn", default="esp32:esp32:XIAO_ESP32S3:USBMode=hwcdc,CDCOnBoot=cdc")
    args = parser.parse_args()
    stage = ROOT/"build/xiao_sketch"
    stage.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT/"firmware/xiao_sense/xiao_sense.ino", stage/"xiao_sketch.ino")
    for name in ("openfault.h", "openfault.c", "telemetry.c"):
        shutil.copy2(ROOT/"firmware/common"/name, stage/name)
    command = ["arduino-cli"]
    if args.config_file:
        command += ["--config-file", str(args.config_file.resolve())]
    subprocess.run(command+["compile", "--fqbn", args.fqbn, "--build-path", str(ROOT/"build/xiao"), str(stage)], check=True)
if __name__ == "__main__":
    main()
