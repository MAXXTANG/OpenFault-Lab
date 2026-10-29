"""Strict feature-only firmware telemetry recording and replay (MIT)."""
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from .pipeline import SLUG, dump

FIELDS = {"v", "source", "seq", "uptime_ms", "state", "rms_milli", "dominant_hz", "score_milli", "clipped"}
CONTROL_FIELDS = {"boot": {"type", "target", "mode", "sensors_connected", "sample_rate", "window", "raw_audio_storage"},
                  "calibration_reset": {"type"}, "error": {"type", "error"}}


def integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def validate(event, source):
    if not isinstance(event, dict):
        raise ValueError("Event must be an object")
    if "type" in event:
        kind = event["type"]
        if not isinstance(kind, str) or kind not in CONTROL_FIELDS or set(event)-CONTROL_FIELDS[kind]:
            raise ValueError("Unknown control event or unexpected fields")
        if kind == "boot":
            if event.get("mode") != source or not isinstance(event.get("target"), str) or len(event["target"]) > 64:
                raise ValueError("Boot mode/target mismatch")
            if event.get("raw_audio_storage", False) is not False:
                raise ValueError("Raw-audio storage must be disabled")
            if "sample_rate" in event and event["sample_rate"] != 16000:
                raise ValueError("Unexpected sample rate")
            if "window" in event and event["window"] != 1024:
                raise ValueError("Unexpected window size")
        elif kind == "error":
            if not isinstance(event.get("error"), str) or not SLUG.fullmatch(event["error"]):
                raise ValueError("Invalid device error code")
        return kind
    if set(event) != FIELDS:
        raise ValueError("Telemetry fields differ from v1; raw/extra fields are not accepted")
    if type(event["v"]) is not int or event["v"] != 1 or event["source"] != source:
        raise ValueError("Telemetry version/source mismatch")
    if event["state"] not in ("calibrating", "normal", "anomaly"):
        raise ValueError("Unknown detector state")
    ranges = {"seq": (0, 2**32-1), "uptime_ms": (0, 2**32-1), "rms_milli": (0, 1000),
              "dominant_hz": (0, 8000), "score_milli": (0, 10**9), "clipped": (0, 1024)}
    if any(not integer(event[k], lo, hi) for k, (lo, hi) in ranges.items()):
        raise ValueError("Telemetry values must be in-range integers")
    return "features"


def record(lines, output, session_id, device_id, source, transport="replay"):
    if source not in ("synthetic", "microphone") or transport not in ("replay", "serial", "stdin"):
        raise ValueError("Declare expected source and transport")
    if any(not isinstance(value, str) or not SLUG.fullmatch(value) for value in (session_id, device_id)):
        raise ValueError("Session and device IDs must be anonymous slugs")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    summary = {"version": 1, "session_id": session_id, "device_id": device_id, "source": source,
               "transport": transport, "started_at": datetime.now(timezone.utc).isoformat(),
               "feature_events": 0, "control_events": 0, "boot_events": 0, "calibration_resets": 0,
               "missing_sequence_events": 0, "sequence_wraps": 0, "uptime_wraps": 0,
               "complete": False, "error": None,
               "timing_note": "Host arrival times; not microphone sampling or inference latency"}
    previous = None
    started = time.monotonic()
    try:
        with (output/"events.jsonl").open("x", encoding="utf-8") as stream:
            for line_number, line in enumerate(lines, 1):
                if len(line) > 4096:
                    raise ValueError(f"Oversized event at line {line_number}")
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except (ValueError, UnicodeError):
                    raise ValueError(f"Invalid JSON at line {line_number}") from None
                kind = validate(event, source)
                if kind == "features":
                    if previous is not None:
                        delta = (event["seq"]-previous["seq"]) % 2**32
                        tick_delta = (event["uptime_ms"]-previous["uptime_ms"]) % 2**32
                        if delta == 0 or delta >= 2**31 or tick_delta >= 2**31:
                            raise ValueError("Duplicate/backward sequence or clock without boot event")
                        summary["missing_sequence_events"] += delta-1
                        summary["sequence_wraps"] += event["seq"] < previous["seq"]
                        summary["uptime_wraps"] += event["uptime_ms"] < previous["uptime_ms"]
                    previous = event
                    summary["feature_events"] += 1
                else:
                    summary["control_events"] += 1
                    if kind == "boot":
                        previous = None
                        summary["boot_events"] += 1
                    elif kind == "calibration_reset":
                        summary["calibration_resets"] += 1
                stream.write(json.dumps({"host_elapsed_ms": round((time.monotonic()-started)*1000, 3),
                                         "event": event}, allow_nan=False)+"\n")
                stream.flush()
                if kind == "error":
                    raise ValueError("Device reported error: " + event["error"])
            if not summary["feature_events"]:
                raise ValueError("No feature events recorded")
            summary["complete"] = True
    except (ValueError, OSError, UnicodeError) as error:
        summary["error"] = str(error)
        raise
    except KeyboardInterrupt:
        summary["error"] = "interrupted"
        raise
    finally:
        summary["host_duration_seconds"] = time.monotonic()-started
        dump(output/"session.json", summary)
    return summary
