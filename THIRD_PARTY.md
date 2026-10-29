# Third-party software

Original application code, tests, scripts, and project documentation use the repository MIT License. Downloaded SDKs and toolchains retain their upstream terms and are excluded from Git.

| Component | Version / revision | Upstream license location | Use |
| --- | --- | --- | --- |
| STM32CubeC5 | 2.1.0, `abeee83eb7181ce278c65681196ede45c930a7ec` | SDK `LICENSE.md` and each component's license | Board-generated initialization and startup/linker inputs |
| ST UART polling example | same SDK revision | `examples/hal/uart/echo_polling/LICENSE.md` (SLA0044 Rev6) | Generated board files; not relicensed as MIT |
| STM32C5 HAL drivers | `9cc83edc954b163ab86bf7e2f16a5356c2d38680` | `stm32c5xx_drivers/LICENSE.md` | HAL2 implementation |
| STM32C5 device family pack | `a5f65bc64535cfa723e9d25f58d7ce23d0937aed` | `stm32c5xx_dfp/LICENSE.md` | MCU definitions |
| CMSIS Core | `2327f7224ff212b2436e5a4cadda3288143fd041` | `arch/cmsis/LICENSE.md` | Cortex-M support |
| Arduino ESP32 | 3.3.2 | [Upstream license files](https://github.com/espressif/arduino-esp32/tree/3.3.2) | XIAO build/runtime and ESP_I2S |
| Arm GNU Toolchain | 14.3.Rel1 | Toolchain `share/doc` license notices | Cross compiler and runtime |

Preserve all downloaded license and copyright files. The build creates a local copy of ST's linker script with its original notices and increases its stack reservation from 1 KiB to 4 KiB. Generated files, ST sources, compiled binaries, and toolchains are not committed or covered by the project's MIT grant. Review notices before distributing any combined binary.

Datasets are separate: none are included or licensed by this file.
