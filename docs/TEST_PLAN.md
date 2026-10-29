# Test plan

## Executable host checks

The root CMake/CTest suite checks silence, DC offset removal, an analytic 1 kHz tone, Nyquist/clipping behavior, invalid input, frozen calibration, repeated-event debounce and recovery, non-finite scores, integer timestamp boundaries, and telemetry buffer truncation.

The synthetic demo emits 80 JSON lines. Calibration is 32 windows. A synthetic amplitude step starts at sequence 48; the debounce first signals an anomaly at sequence 50. These checks demonstrate software behavior on constructed inputs, not fault-detection performance.

## Hardware acceptance

### XIAO

- Verify board identity, current firmware backup needs, and the correct USB port before upload.
- Boot must report XIAO microphone mode, 16 kHz, 1024 samples, and no raw-audio storage.
- A normal running machine must complete calibration; `r` must reset calibration.
- Inspect silence, steady noise, safe controlled amplitude changes, clipping, and serial reconnection.
- Measure actual processing duration, DMA overflow count, memory and data throughput before claiming continuous acquisition.

### STM32

- Inspect board revision, oscillator and ST-LINK VCP bridges first.
- Flash via SWD only after confirming the connected target; no automatic flash is performed by this project's build scripts.
- At 115200 8N1, boot must report synthetic mode and no connected sensors.
- Verify the repeated normal/amplitude-step sequence and local reset behavior.
- Measure stack high-water and elapsed processing time before enabling sensor acquisition.

Future evaluation needs labeled controlled sessions, session/device-separated train/test data, precision/recall, false alarms per hour, latency, and resource use. None of these measured performance results exist yet.
