# Hardware

Target board: **NUCLEO-C5A3ZG**. The board and all connections still require project-specific verification.

The first bench setup is planned around an external MEMS microphone, a three-axis accelerometer, a small low-voltage DC fan or motor, an appropriate power supply, guards, a fixture, and wiring. The board does not supply the planned microphone or accelerometer.

No sensor part number or pin assignment is approved yet. P0 must check the exact official board schematic, MCU pin multiplexing, voltages, timing, DMA, and Ethernet conflicts before publishing a wiring diagram or connecting hardware.

Use safe, controlled operating variations. Do not damage equipment or alter rotating blades to create anomalies. Record fixture and sensor placement so measurements can be repeated.

## Available development hardware

The maintainer confirmed a XIAO ESP32S3 Sense on October 29, 2026. Its built-in PDM microphone is the first acquisition path, using GPIO42 clock and GPIO41 data per Seeed documentation. No extra microphone wiring is required for that target. The camera and SD card are unused. An accelerometer and external STM32 microphone remain unselected.
