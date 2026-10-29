#!/usr/bin/env python3
"""Record validated summary events from a replay file, stdin, or a read-only serial port (MIT)."""
import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"host"))
from openfault.events import record


@contextmanager
def serial_lines(port, seconds):
    # macOS/Linux only. No upload command, serial writes, explicit DTR manipulation, or discovery.
    import select
    import termios
    fd = os.open(port, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK)
    original = None
    try:
        original = termios.tcgetattr(fd)
        config = termios.tcgetattr(fd)
        config[:4] = [0, 0, termios.CS8 | termios.CREAD | termios.CLOCAL, 0]
        config[4:6] = [termios.B115200, termios.B115200]
        config[6][termios.VMIN] = 0
        config[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW, config)
        def generate():
            deadline = time.monotonic()+seconds
            pending = b""
            while time.monotonic() < deadline:
                if not select.select([fd], [], [], min(0.5, max(0, deadline-time.monotonic())))[0]:
                    continue
                data = os.read(fd, 4096)
                if not data:
                    raise ValueError("Serial port disconnected")
                pending += data
                while b"\n" in pending:
                    line, pending = pending.split(b"\n", 1)
                    if len(line) > 4096:
                        raise ValueError("Oversized serial event")
                    yield line.decode("utf-8")
                if len(pending) > 4096:
                    raise ValueError("Oversized serial event")
            if pending:
                raise ValueError("Capture ended with an incomplete serial line")
        yield generate()
    finally:
        try:
            if original is not None:
                termios.tcsetattr(fd, termios.TCSANOW, original)
        finally:
            os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input", help="JSONL file, or - for stdin")
    input_group.add_argument("--port", help="Explicit macOS/Linux serial port, read only")
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--device-id", required=True)
    parser.add_argument("--source", choices=("synthetic", "microphone"), required=True)
    args = parser.parse_args()
    if not 0 < args.seconds <= 86400:
        parser.error("--seconds must be finite, positive and at most 86400")
    def capture(lines, transport):
        return record(lines, args.out, args.session_id, args.device_id, args.source, transport)
    try:
        if args.port:
            with serial_lines(args.port, args.seconds) as lines:
                summary = capture(lines, "serial")
        elif args.input == "-":
            summary = capture(iter(lambda: sys.stdin.readline(4097), ""), "stdin")
        else:
            with Path(args.input).open(encoding="utf-8") as stream:
                summary = capture(iter(lambda: stream.readline(4097), ""), "replay")
        print(f"Saved {summary['feature_events']} events; missing sequence events: {summary['missing_sequence_events']}; {args.out}")
    except (OSError, ValueError, UnicodeError, ImportError) as error:
        parser.exit(2, f"Event capture failed: {error}\n")
    except KeyboardInterrupt:
        parser.exit(130, "Capture interrupted; partial validated data and session summary were preserved\n")
if __name__ == "__main__":
    main()
