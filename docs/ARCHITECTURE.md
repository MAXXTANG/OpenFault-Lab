# First firmware increment

Design review: October 29, 2026. The maintainer has a **XIAO ESP32S3 Sense**. Availability of the STM32 board and external accelerometer is not confirmed.

## Decisions

Implement one original, allocation-free C signal-processing core, shared by native tests, STM32 firmware, and an Arduino XIAO microphone sketch. Use 16 kHz, signed PCM16, 1024-sample non-overlapping windows (64 ms). Compute DC-removed RMS, peak, clipping count, zero-crossing rate, Hann-windowed FFT dominant frequency, and spectral centroid. Normalize amplitudes to full scale; these are not calibrated sound-pressure measurements.

The initial anomaly baseline models only AC RMS using Welford statistics over 32 windows. Freeze it after calibration, apply a minimum standard-deviation floor, and require three consecutive high scores. It is a demonstrator of amplitude change, not a trained fault classifier. Frequency features are reported but do not yet affect the score. Calibrate with the machine already running normally; reset to recalibrate when speed or installation changes.

Both targets report newline-delimited JSON summaries. STM32 runs explicitly labeled synthetic data until sensors are selected. XIAO uses its built-in PDM microphone. There is no vibration capture, raw-audio persistence, SD, camera, Wi-Fi, Ethernet, or TinyML in this increment.

## Verified integration boundary

- ST's STM32CubeC5 **2.1.0**, commit `abeee83eb7181ce278c65681196ede45c930a7ec`, includes a generated NUCLEO-C5A3ZG UART polling configuration. Reuse its initialization, startup, linker script, and dependencies unchanged from a local pinned checkout.
- That configuration uses USART2, **PA2 TX / PA3 RX, AF7, 115200 8N1**, marked DBGIN VCP in the generated source. Its clock setup selects 144 MHz via a 48 MHz HSE reference. Physical board revision, oscillator, solder bridges, and actual VCP routing still require inspection.
- Seeed's Sense microphone documentation specifies **PDM clock GPIO42 / data GPIO41**, PCM16 mono at 16 kHz. Use the Arduino ESP32 3.x `ESP_I2S` interface; pin Arduino core **3.3.2**. Availability on this machine does not prove operation on the owner's hardware.

Sources and version details: [TECH_RESEARCH.md](TECH_RESEARCH.md).

## Memory estimate

At PCM16 mono, a one-second ring costs 32,000 bytes. A 1024-sample PCM window is 2,048 bytes; separate 1024-float real/imaginary FFT arrays cost 8,192 bytes. Shared core plus PCM therefore needs approximately 10 KiB, excluding small metadata and runtime. A 2048-window equivalent would need 20 KiB. This increment uses streaming windows rather than the one-second ring. Target `.map` / `size` measurements must replace these estimates after linking; stack, driver, DMA, and network budgets are separate.

## Deferred hardware gates

External STM32 microphone, accelerometer, I2S/I2C pins, DMA timing, cross-sensor synchronization, and Ethernet allocation remain unresolved. Those drivers must wait for exact parts and pin-conflict review. This review clears UART bring-up and the portable core only, not the full sensor design.
