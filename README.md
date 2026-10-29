# OpenFault Lab

**Open-source acoustic and vibration monitoring with STM32C5.**

When a small fan or motor starts making an unusual noise, it can be hard to tell what changed. Speed, mounting conditions, and background noise all affect what we hear. OpenFault Lab explores whether a low-cost microcontroller can establish a machine's normal operating baseline and recognize changes worth investigating.

## Status

The first implementation includes a shared C processing core, native tests, a **XIAO ESP32S3 Sense microphone** sketch, and an **STM32C5 synthetic UART** target. Native checks and target builds are tracked in [validation](docs/VALIDATION.md). No hardware execution, real-machine detection accuracy, or continuous-capture performance is claimed.

The maintainer has a XIAO ESP32S3 Sense for early microphone experiments. The final development board remains **NUCLEO-C5A3ZG**; its availability and external sensor configuration still need confirmation.
The project is being prepared for the **STM32Cube Innovation Challenge**, with an internal completion target of **January 28, 2027**. Receiving a free development board is not assumed.

## First experiment

The initial demonstrator will use a small, guarded, low-voltage DC fan or motor, an external MEMS microphone, and a three-axis accelerometer. Using the STM32Cube ecosystem, the STM32C5 will acquire sensor data, extract time-domain and FFT features, and calculate an anomaly score against a per-machine baseline.

The first implementation will use a transparent signal-processing baseline. A compact TinyML model will be compared with it if measured memory and processing budgets permit. The aim is to find out where machine learning helps, including reporting when it does not.

UART logs will provide the first complete output path. Ethernet will then send derived features, scores, and event summaries to a local dashboard. Normal monitoring will not store or transmit raw audio.

```text
External microphone + accelerometer
                |
       Acquisition and windows
                |
       Time-domain / FFT features
                |
      Baseline and anomaly scoring
                |
       UART / local Ethernet output
```

## How it will be evaluated

- Record normal operation across speeds, mounting conditions, and background noise.
- Compare it with safe, controlled variations in speed, guarded airflow, and mounting.
- Split training and test data by recording session or device, before creating overlapping windows.
- Report precision, recall, false alerts per hour, processing time, and firmware memory use.
- Describe the test conditions and limits instead of claiming general fault diagnosis or remaining useful life prediction.

Any public sample recordings will come from controlled bench tests with permissions and a separate, explicit dataset license. Synthetic signals, if used, will be labeled as synthetic.

## Repository guide

| Path | Purpose |
| --- | --- |
| [firmware/common/openfault.h](firmware/common/openfault.h) | Shared PCM16 features and detector API |
| [firmware/xiao_sense/README.md](firmware/xiao_sense/README.md) | Current XIAO microphone build and calibration |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Phases and the first feasibility checklist |
| [docs/VALIDATION.md](docs/VALIDATION.md) | What has and has not been verified |
| [hardware/README.md](hardware/README.md) | Planned bench hardware and wiring gates |
| [firmware/stm32c5/README.md](firmware/stm32c5/README.md) | STM32C5 firmware scope and toolchain status |
| [dataset/README.md](dataset/README.md) | Data provenance, splits, and release rules |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |

## Run the native checks

```sh
cmake -S . -B build/host -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/host
ctest --test-dir build/host --output-on-failure
./build/host/synthetic_demo
```

Requirements: C11 compiler, CMake, Ninja, and Python 3. The demo emits synthetic JSON events; it is not microphone data.

For target builds, see the [XIAO microphone guide](firmware/xiao_sense/README.md) and [STM32 UART guide](firmware/stm32c5/README.md). Neither build helper flashes a device. Review [architecture](docs/ARCHITECTURE.md), [test plan](docs/TEST_PLAN.md), and [known risks](docs/RISK_REGISTER.md) before hardware testing.

## References

- [STM32Cube Innovation Challenge](https://www.elektormagazine.com/stm32cube-innovation-challenge)
- [Challenge rules](https://www.elektormagazine.com/stm32cube-terms-conditions)
- [NUCLEO-C5A3ZG product page](https://www.st.com/en/evaluation-tools/nucleo-c5a3zg.html)
- [STM32C5A3ZG product page](https://www.st.com/en/microcontrollers-microprocessors/stm32c5a3zg.html)

## License

Original project code and documentation in this repository are released under the [MIT License](LICENSE). Third-party components retain their own licenses and must be identified when added. Datasets require their own release terms; no dataset is currently included.
