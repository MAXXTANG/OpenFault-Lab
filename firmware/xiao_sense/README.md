# XIAO ESP32S3 Sense microphone firmware

This development target uses the built-in PDM microphone to exercise the shared processing core while STM32 hardware is unavailable. It is not the final STM32 competition target.

## Build

Use Arduino CLI and the official Espressif **3.3.2** core. With an existing Arduino configuration:

```sh
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.3.2 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
python3 tools/build_xiao.py
```

For a separate local Arduino configuration, pass `--config-file <yaml>` to the build helper. In the maintainer's initial workspace the configuration is `.tools/arduino-cli.yaml` (ignored by Git). The helper copies the sketch and shared C files into `build/xiao_sketch/` and compiles into `build/xiao/`. It never uploads.

Default FQBN: `esp32:esp32:XIAO_ESP32S3:USBMode=hwcdc,CDCOnBoot=cdc`. The sketch uses Seeed's documented PDM clock GPIO42 and data GPIO41, PCM16 mono at 16 kHz. It does not enable the camera, SD card, Wi-Fi or raw-audio storage.

## First device test

After confirming the USB port, upload using Arduino IDE or CLI; flashing replaces the board's current firmware. In Arduino IDE, place `openfault.h`, `openfault.c` and `telemetry.c` alongside the sketch, or open the staged `build/xiao_sketch` folder created by the helper. Select **XIAO_ESP32S3**, hardware CDC and USB CDC on boot.

Open the serial monitor at 115200. Start the machine in its normal operating condition, then reset the board or send `r` to calibrate. The first 32 windows establish the RMS baseline (nominally 2.048 seconds, plus processing time); then JSON events report `normal` or `anomaly`. The initial score uses only RMS, not a trained fault model. `r` resets the baseline after a change of speed or installation.

JSON contains summaries only. `rms_milli` is normalized amplitude multiplied by 1000; it is not dB SPL. `score_milli` is the standardized RMS deviation multiplied by 1000. On processing/read/serial failure the sketch reports an error and stops until reset.

Compilation is separate from hardware verification. See [validation](../../docs/VALIDATION.md); continuous sampling, DMA overruns, USB disconnects and processing deadlines still need measurement on the actual board.

A CLI upload, after verifying the connected USB port, can use the existing build output:

```sh
arduino-cli --config-file .tools/arduino-cli.yaml upload \
  --fqbn 'esp32:esp32:XIAO_ESP32S3:USBMode=hwcdc,CDCOnBoot=cdc' \
  --port 'YOUR_CONFIRMED_USB_PORT' --input-dir build/xiao
```

The `.tools` configuration is specific to the maintainer workspace. Omit that option when using your own Arduino configuration. This upload command has not been executed in the initial validation.
