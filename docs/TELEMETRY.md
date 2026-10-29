# Feature telemetry and session logging

Current firmware emits UTF-8, newline-delimited JSON v1 summaries. No raw samples are transmitted. `tools/record_events.py` accepts only the defined summary/control fields; extra fields such as PCM arrays are rejected before storage.

## Offline replay now

```sh
./build/host/synthetic_demo > build/synthetic-events.jsonl
python3 tools/record_events.py \
  --input build/synthetic-events.jsonl --source synthetic \
  --session-id replay_01 --device-id simulated_fan \
  --out outputs/replay_01
```

Use `--input -` for stdin. The destination must be new. The recorder writes validated events to `events.jsonl`, wrapped with a host-arrival elapsed time. `session.json` records provenance, completion status, counts, missing sequence events, wraps, boots and calibration resets. Invalid lines are not stored; a failed capture preserves the valid prefix and marks the session incomplete. It does not infer ground-truth labels or report accuracy from firmware predictions alone.

## Explicit serial capture later

After hardware is flashed and its USB port is verified:

```sh
python3 tools/record_events.py \
  --port 'YOUR_CONFIRMED_USB_PORT' --seconds 60 --source microphone \
  --session-id fan_normal_01 --device-id bench_fan_01 \
  --out outputs/fan_normal_01
```

The serial adapter supports macOS/Linux at 115200 8N1 and restores terminal settings on exit. It opens only the explicit port and sends no writes, upload commands or explicit DTR controls. Opening a port may still affect hardware through the OS driver; actual USB-device behavior has not been tested. The adapter was tested against a software pseudo-terminal only. It never discovers devices automatically or records raw audio.

The time limit ends the capture. If it ends inside a JSON line, that session is marked incomplete rather than silently dropping the fragment. Ctrl-C also preserves a partial session with an interrupted status. The next capture must use a new session folder.

## v1 feature fields

| Field | Meaning |
| --- | --- |
| `v` | Exactly integer 1 |
| `source` | `synthetic` or `microphone`; must match the explicit logger argument |
| `seq` | Unsigned 32-bit event sequence |
| `uptime_ms` | Unsigned 32-bit device uptime, not wall-clock time |
| `state` | `calibrating`, `normal`, or `anomaly` |
| `rms_milli` | Normalized AC RMS × 1000, truncated to integer; not dB SPL |
| `dominant_hz` | Integer dominant frequency, 0–8000 Hz |
| `score_milli` | RMS baseline deviation score × 1000, truncated to integer |
| `clipped` | Samples equal to PCM16 min/max, 0–1024 |

The logger validates bounds, integer types, version, expected source and exact feature field names. Rounded v1 telemetry is not a lossless replacement for full-precision offline features.

## Control events and continuity

`type=boot` identifies the target and mode. XIAO also supplies sample rate/window size and `raw_audio_storage=false`; STM32 supplies `sensors_connected=false` in its synthetic mode. `type=calibration_reset` marks a new baseline without resetting sequence numbers. `type=error` supplies a short device error code and makes the capture incomplete.

Within a boot epoch, the logger accepts modulo-2^32 sequence/uptime wrap, counts forward sequence gaps, and rejects duplicate/backward sequences or an unexplained clock reversal. A validated boot begins a new epoch. Gaps remain visible in the summary even if the capture otherwise reaches its endpoint; a complete capture is not a guarantee of lossless sampling. Firmware DMA overruns can occur without sequence gaps and still require on-device instrumentation.

Host arrival timing includes USB buffering and computer scheduling. It cannot measure sample rate, inference latency or DMA continuity. The logger does not merge epochs into a waveform evaluation session.
