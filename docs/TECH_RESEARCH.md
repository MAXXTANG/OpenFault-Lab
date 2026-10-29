# Integration sources

Reviewed October 29, 2026. Source availability is distinct from a successful local build or hardware test.

| Topic | Pinned official reference | Finding |
| --- | --- | --- |
| Board | [ST product page](https://www.st.com/en/evaluation-tools/nucleo-c5a3zg.html) | NUCLEO-C5A3ZG; physical board revision unconfirmed |
| SDK | [STM32CubeC5 2.1.0](https://github.com/STMicroelectronics/STM32CubeC5/tree/2.1.0) | Commit `abeee83eb7181ce278c65681196ede45c930a7ec` |
| UART configuration | [mx_usart2.c](https://github.com/STMicroelectronics/STM32CubeC5/blob/2.1.0/examples/hal/uart/echo_polling/NUCLEO-C5A3ZG/generated/hal/mx_usart2.c) | HAL2 handle/config types; 115200 8N1, PA2/PA3 AF7 |
| Clock | [mx_rcc.c](https://github.com/STMicroelectronics/STM32CubeC5/blob/2.1.0/examples/hal/uart/echo_polling/NUCLEO-C5A3ZG/generated/hal/mx_rcc.c) | 48 MHz HSE reference, PSIS 144 MHz; actual board not measured |
| HAL2 | [2.1.0 release notes](https://dev.st.com/stm32cube-docs/stm32c5xx-hal-drivers/2.1.0/en/release_notes.html) | Use SDK-supplied declarations, not HAL1 examples |
| MCU definitions | [stm32c5xx-dfp](https://github.com/STMicroelectronics/stm32c5xx-dfp/tree/a5f65bc64535cfa723e9d25f58d7ce23d0937aed) | Startup and linker selected for STM32C5A3ZGT6 |
| XIAO microphone | [Seeed Sense microphone guide](https://wiki.seeedstudio.com/xiao_esp32s3_sense_mic/) | GPIO42 clock / GPIO41 data, PDM RX, 16 kHz PCM16 mono |
| Arduino core | [Espressif 3.3.2](https://github.com/espressif/arduino-esp32/tree/3.3.2) | Use ESP_I2S; no legacy I2S API mixing |
| Arm GCC | [Arm GNU Toolchain](https://developer.arm.com/Tools%20and%20Software/GNU%20Toolchain) | Local build uses 14.3.Rel1 / GCC 14.3.1 |

The ST sample's initialization is already generated. This project has not installed or run STM32CubeMX2 and does not claim to have regenerated its configuration.

## Dependencies and licenses

Keep downloaded dependencies under ignored `.deps/` and tools under `.tools/`; do not relicense them as project MIT code. See [THIRD_PARTY.md](../THIRD_PARTY.md). ST example code carries SLA0044; its generated HAL configuration also carries its own license. A public repository of original MIT application code does not change those terms. Do not publish combined firmware binaries without their required notices and license review.

## Open research

No external STM32 sensor pin map is approved. I2S microphone compatibility, ADC fallback conditioning, IMU bandwidth, sensor alignment, DMA routing, Ethernet conflicts, and complete BOM need dedicated research after actual parts are selected. XIAO is a development aid; final competition hardware remains STM32C5.
