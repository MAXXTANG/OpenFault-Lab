# Validation status

Executed on October 29, 2026, on macOS Apple Silicon. Local build/test results below do not demonstrate operation on either physical board.

| Area | Status | Evidence / limits |
| --- | --- | --- |
| Shared C signal processing | PASS, native | Silence, DC removal, 1 kHz tone, two-tone centroid, Nyquist/clipping, invalid inputs |
| RMS baseline and events | PASS, native | Calibration, variance floor and measured-variance branch, frozen baseline, debounce and recovery |
| JSON serialization | PASS, native | 80 parsed synthetic events; bounds and integer timestamp checks |
| Offline WAV pipeline | PASS, native | Shared C reader, normal-only train fit, session/device leakage checks, metrics and report |
| Event recorder | PASS, replay and virtual terminal | Source/schema/sequence/boot validation, valid-prefix preservation; no physical serial device |
| Host integration cases | PASS, 17 Python tests | Executed inside the offline_pipeline CTest target |
| Address/undefined behavior sanitizers | PASS, native | All three CTest targets with Clang ASan + UBSan |
| STM32C5 cross build | PASS | GCC 14.3.1; ST CubeC5/HAL2 2.1.0; ELF/BIN/MAP generated |
| XIAO microphone cross build | PASS | Arduino CLI 1.5.1; ESP32 core 3.3.2; XIAO_ESP32S3 with hardware CDC |
| Physical flash / boot | NOT EXECUTED | Neither target has been flashed by this work |
| Sensor acquisition and continuous timing | NOT EXECUTED | XIAO wiring follows Seeed guide; actual sample rate, overruns and timing unmeasured |
| STM32 external sensors | NOT IMPLEMENTED | Exact microphone, accelerometer and pin map still pending |
| Detection accuracy / false alarms | NOT MEASURED | No real dataset or labeled hardware sessions |
| TinyML / Ethernet | NOT IMPLEMENTED | Later increments |

## Executed native commands

```sh
cmake -S . -B build/host -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/host
ctest --test-dir build/host --output-on-failure
cmake -S . -B build/sanitize -G Ninja -DCMAKE_BUILD_TYPE=Debug \
  '-DCMAKE_C_FLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer'
cmake --build build/sanitize
ctest --test-dir build/sanitize --output-on-failure
```

Both native builds now pass **3/3 CTest targets**, including **17 Python integration tests** in the offline pipeline target. Versions: Apple Clang 21.0.0, CMake 4.1.2, Ninja 1.13.1, Python 3.14.6. The synthetic integration case first reports an anomaly at sequence 50, after an amplitude step at 48; these are constructed software inputs.

## Executed STM32 commands and linked memory

```sh
python3 tools/fetch_st_sdk.py
python3 tools/build_stm32.py --fresh
```

The SDK-fetch helper was exercised against an existing pinned checkout; fresh-clone behavior follows the same Git commands but was not independently repeated end-to-end. CMake verifies the parent SDK and three dependency commit IDs.

- Flash allocation: **15,744 bytes** (text 15,648 + initialized data 96).
- RAM allocation: **15,656 bytes**, including the 4 KiB reserved stack and 512-byte heap.
- These are linker allocations, not measured stack/heap high-water marks or CPU load.
- Newlib `nosys` emits linker warnings for unimplemented file I/O stubs (`_read`, `_write`, `_close`, `_lseek`). The application sends telemetry directly through HAL UART and does not use file I/O; hardware execution is still required to verify startup/runtime behavior.
- ST-generated initialization is reused, not regenerated locally with STM32CubeMX2.

For future measurements, record the date, revision, tools, board revision, fixture, command/procedure, and actual output. Do not report synthetic tests as real-machine performance.

## Executed XIAO build

```sh
python3 tools/build_xiao.py --config-file .tools/arduino-cli.yaml
```

- Build result: **318,291 bytes** program storage; **30,824 bytes** global dynamic-memory allocation (Arduino report).
- Outputs under `build/xiao/`; sources staged under `build/xiao_sketch/`.
- These numbers exclude runtime stack/heap high-water and do not measure acquisition timing.
- Local serial discovery showed only generic debug/Bluetooth ports and no identifiable XIAO USB target. No upload or microphone recording was performed.
- The GitHub native workflow is provided; its remote run is separate from the executed local checks above.

## Executed no-flash workflow (increment 2)

The existing firmware sources and target binaries were not changed by this increment, so the previous target builds were not repeated. New code is confined to native extraction, host analysis/recording, tests and documentation.

```sh
cmake -S . -B build/host -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/host
ctest --test-dir build/host --output-on-failure
cmake -S . -B build/sanitize -G Ninja -DCMAKE_BUILD_TYPE=Debug \
  '-DCMAKE_C_FLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer'
cmake --build build/sanitize
ctest --test-dir build/sanitize --output-on-failure
python3 tools/offline.py demo --out outputs/offline_demo_20261029
./build/host/synthetic_demo > build/synthetic-events.jsonl
python3 tools/record_events.py --input build/synthetic-events.jsonl \
  --source synthetic --session-id host_replay_01 --device-id simulated_fan \
  --out outputs/telemetry_replay_20261029
```

Results:

- Both native suites passed 3/3 CTest targets. All 17 host integration cases passed with the normal and sanitized C extractor.
- The complete offline demo generated five deterministic synthetic WAV sessions, trained only on two normal sessions, and evaluated three held-out sessions.
- Expected synthetic outcome: 30 true positives, 0 false positives, 224 true negatives and 34 false negatives. One of two variation intervals was detected: amplitude change was detectable, equal-amplitude frequency change was missed. This tests both intended behavior and an explicit RMS-only limitation; it is not measured accuracy.
- The detected interval's nominal sample-timeline delay was 192 ms (three windows), not measured MCU inference latency. Normal exposure was only 14.336 seconds, so zero false episodes does not establish real-world reliability.
- Replayed and validated 80 feature-only firmware-format JSON events, with no missing sequence events. No raw audio was recorded by the logger.
- Exercised the serial adapter against a POSIX pseudo-terminal only. No real USB port, camera, microphone, firmware upload or flash command was used in this increment.
- Opened the final generated HTML report locally and visually checked the synthetic-data banner, metrics, normal/amplitude/frequency plots and limitations. It contains no raw audio or external assets.
- Local generated WAVs, results, screenshots and capture logs stay under ignored `outputs/`; only the original tooling, template and documentation are committed.

A second evaluation of the same synthetic inputs into `evaluation_final/` exercised the standalone evaluate command and produced the report used for visual QA. Existing output directories were never overwritten.
