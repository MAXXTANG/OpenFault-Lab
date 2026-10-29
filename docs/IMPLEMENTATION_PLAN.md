# Implementation plan

## Increment 1: current

- Portable PCM16 window processing, FFT features, RMS calibration and debounce.
- Native synthetic tests and a demo with explicitly labeled synthetic events.
- STM32C5 HAL2 UART bring-up with generated ST initialization, with synthetic input only.
- XIAO ESP32S3 Sense PDM microphone path using the same core; raw samples are not persisted.
- Build instructions, third-party boundaries, and honest validation records.

## Increment 2: no-flash host workflow

The WAV feature-extraction CLI, session-separated frozen-baseline evaluation, deterministic synthetic experiment, JSON/HTML reports and feature-only event recorder are implemented. Native tests cover leakage rejection, malformed recordings, event continuity, error recovery and a software pseudo-terminal. See [OFFLINE_WORKFLOW.md](OFFLINE_WORKFLOW.md).

No real recordings or actual serial-device interaction are required for this increment. Remaining real-data and hardware claims stay unverified.

## Next: device verification

1. Connect the XIAO over USB and inspect its boot/event stream after flashing the locally built sketch.
2. Measure processing time, microphone signal range, serial throughput, stack/heap usage, and DMA overrun behavior. Do not assume 16 kHz operation merely because initialization succeeds.
3. Collect separate controlled sessions at known speeds, with fixtures and timestamps; add an explicit opt-in capture mode before saving raw audio.
4. Verify the physical STM32 board revision, HSE and VCP routing; run its synthetic firmware and measure actual memory high-water marks.
5. Select the STM32 microphone and accelerometer, finish pin/timing review, then integrate acquisition separately. Reassess buffer ownership and interrupts before enabling DMA.
6. Expand beyond the scalar RMS baseline, evaluate by session/device, then consider TinyML and Ethernet.

The user requested implementation to begin; this increment implements the reviewed core/UART boundary. The complete multisensor P0 review is still open.
