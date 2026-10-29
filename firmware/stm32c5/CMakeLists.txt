cmake_minimum_required(VERSION 3.20)
project(openfault_stm32c5 C ASM)
set(CMAKE_C_STANDARD 11)
set(ST_CUBE_ROOT "" CACHE PATH "Pinned STM32CubeC5 2.1.0 checkout")
if(NOT EXISTS "${ST_CUBE_ROOT}/stm32c5xx_drivers/hal/stm32c5xx_hal_uart.c")
  message(FATAL_ERROR "Run tools/fetch_st_sdk.py, then pass -DST_CUBE_ROOT=<checkout>")
endif()
execute_process(COMMAND git -C "${ST_CUBE_ROOT}" rev-parse HEAD OUTPUT_VARIABLE st_revision OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ERROR_IS_FATAL ANY)
if(NOT st_revision STREQUAL "abeee83eb7181ce278c65681196ede45c930a7ec")
  message(FATAL_ERROR "Unsupported ST SDK revision: ${st_revision}")
endif()
foreach(dependency IN ITEMS
    "arch/cmsis|2327f7224ff212b2436e5a4cadda3288143fd041"
    "stm32c5xx_dfp|a5f65bc64535cfa723e9d25f58d7ce23d0937aed"
    "stm32c5xx_drivers|9cc83edc954b163ab86bf7e2f16a5356c2d38680")
  string(REPLACE "|" ";" parts "${dependency}")
  list(GET parts 0 dependency_path)
  list(GET parts 1 dependency_revision)
  execute_process(COMMAND git -C "${ST_CUBE_ROOT}/${dependency_path}" rev-parse HEAD
    OUTPUT_VARIABLE found_revision OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ERROR_IS_FATAL ANY)
  if(NOT found_revision STREQUAL dependency_revision)
    message(FATAL_ERROR "Unexpected ${dependency_path} revision; run tools/fetch_st_sdk.py")
  endif()
endforeach()
set(board "${ST_CUBE_ROOT}/examples/hal/uart/echo_polling/NUCLEO-C5A3ZG")
set(device "${board}/user_modifiable/Device/STM32C5A3ZGT6")
set(gen "${board}/generated/hal")
set(driver "${ST_CUBE_ROOT}/stm32c5xx_drivers")
set(core "${CMAKE_CURRENT_LIST_DIR}/../common")
# Preserve ST's script notices; modify only a generated build-local copy.
# Reserve 4 KiB stack until on-target high-water measurements are available.
file(READ "${device}/stm32c5a3xg_flash.ld" linker_script)
string(REPLACE "STACK_SIZE = 0x400;" "STACK_SIZE = 0x1000;" linker_script "${linker_script}")
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/stm32c5a3xg_flash.ld" "${linker_script}")
add_executable(openfault.elf main.c "${core}/openfault.c" "${core}/telemetry.c"
  "${device}/startup_stm32c5a3xx.c" "${device}/system_stm32c5xx.c"
  "${gen}/mx_system.c" "${gen}/mx_rcc.c" "${gen}/mx_cortex_mpu.c"
  "${gen}/mx_cortex_nvic.c" "${gen}/mx_gpio_default.c" "${gen}/mx_icache.c" "${gen}/mx_usart2.c")
foreach(module hal hal_cortex hal_rcc hal_gpio hal_icache hal_uart hal_pwr hal_flash_itf hal_dma hal_q)
  target_sources(openfault.elf PRIVATE "${driver}/hal/stm32c5xx_${module}.c")
endforeach()
target_include_directories(openfault.elf PRIVATE "${core}" "${gen}"
  "${driver}/hal" "${driver}/ll" "${driver}/timebases"
  "${ST_CUBE_ROOT}/stm32c5xx_dfp/Include" "${ST_CUBE_ROOT}/arch/cmsis/CMSIS/Core/Include")
target_compile_definitions(openfault.elf PRIVATE STM32C5A3xx USE_EXTERNAL_ENV)
set(cpu -mcpu=cortex-m33 -mthumb -mfpu=fpv5-sp-d16 -mfloat-abi=hard)
target_compile_options(openfault.elf PRIVATE ${cpu} -Os -g3 -ffunction-sections -fdata-sections -fstack-usage -Wall -Wextra -Werror=implicit-function-declaration)
target_link_options(openfault.elf PRIVATE ${cpu} --specs=nano.specs --specs=nosys.specs
  "-T${CMAKE_CURRENT_BINARY_DIR}/stm32c5a3xg_flash.ld" -Wl,--gc-sections -Wl,--print-memory-usage "-Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/openfault.map")
target_link_libraries(openfault.elf PRIVATE m)
add_custom_command(TARGET openfault.elf POST_BUILD
  COMMAND arm-none-eabi-objcopy -O binary $<TARGET_FILE:openfault.elf> "${CMAKE_CURRENT_BINARY_DIR}/openfault.bin"
  COMMAND arm-none-eabi-size $<TARGET_FILE:openfault.elf>)
