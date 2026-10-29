"""Validate serialized synthetic events, not measured detection performance."""
import json
import subprocess
import sys
events = [json.loads(line) for line in subprocess.check_output([sys.argv[1]], text=True).splitlines()]
assert len(events) == 80
assert all(x["source"] == "synthetic" for x in events)
assert all(x["state"] == "calibrating" for x in events[:32])
assert all(x["state"] == "normal" for x in events[32:50])
assert all(x["state"] == "anomaly" for x in events[50:])
assert all(x["dominant_hz"] == 1000 for x in events)
assert [x["seq"] for x in events] == list(range(80))
assert set(events[0]) == {"v", "source", "seq", "uptime_ms", "state", "rms_milli", "dominant_hz", "score_milli", "clipped"}
print("PASS: 80 synthetic JSON events, calibration and debounced transition")
