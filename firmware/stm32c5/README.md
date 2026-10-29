# STM32C5 firmware

No firmware is included yet. The target is NUCLEO-C5A3ZG using the STM32Cube ecosystem.

Before adding generated or handwritten firmware, complete the P0 design review and record supported toolchain, MCU package, and HAL versions. Verify interfaces and APIs against STM32C5 documentation rather than copying another STM32 family's pin map or driver calls.

The planned bring-up order is build/flash and UART, microphone acquisition, accelerometer acquisition, streaming DSP, baseline scoring, and local Ethernet summaries. Add exact build, flash, and test instructions only after executing them. Preserve all ST and other third-party licenses.
