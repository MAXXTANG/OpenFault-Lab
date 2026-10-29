# STM32C5 UART bring-up

Target: NUCLEO-C5A3ZG. This increment boots ST's generated HAL2 system initialization, processes **synthetic** PCM windows, and sends newline-delimited JSON over USART2. There are no external sensor drivers yet.

## Build

Install CMake, Ninja, Python 3, Git and Arm GNU Toolchain **14.3.Rel1** (GCC 14.3.1). Add its `bin` directory to `PATH`, then run from the repository root:

```sh
python3 tools/fetch_st_sdk.py
cmake -S firmware/stm32c5 -B build/stm32c5 -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$PWD/firmware/stm32c5/arm-gcc.cmake" \
  -DST_CUBE_ROOT="$PWD/.deps/STM32CubeC5"
cmake --build build/stm32c5
```

Alternatively, `python3 tools/build_stm32.py` uses the same settings (add `--fresh` if relocating a cached toolchain).

Outputs: `build/stm32c5/openfault.elf`, `openfault.bin`, `openfault.map` and per-source `.su` stack reports. Build commands never flash hardware.

The fetch helper pins STM32CubeC5 to **2.1.0**, commit `abeee83eb7181ce278c65681196ede45c930a7ec`, and initializes only required submodules. The build reuses its NUCLEO-C5A3ZG generated configuration and startup; STM32CubeMX2 regeneration has not been tested. A build-local linker-script copy preserves ST notices and increases the stack reservation to 4 KiB.

## Hardware check before flash

The reference configuration uses USART2 TX **PA2**, RX **PA3**, AF7, **115200 8N1**, and a 48 MHz HSE reference to select 144 MHz. Confirm the exact board revision, oscillator and ST-LINK VCP solder-bridge routing before relying on this configuration.

After a verified flash, the expected boot event identifies `mode=synthetic` and `sensors_connected=false`. A generated 1 kHz tone changes amplitude halfway through a 128-window cycle. Events remain labeled `source=synthetic`; no measured timing or detection performance is implied by these generated data.

ST's source and generated files keep their own licenses. See [third-party notices](../../THIRD_PARTY.md) and [validation](../../docs/VALIDATION.md). Do not publish combined binaries without the required license review and notices.
