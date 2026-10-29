# OpenFault Lab

**Open-source acoustic and vibration monitoring with STM32C5.**

When a small fan or motor starts making an unusual noise, it can be hard to tell what changed. Speed, mounting conditions, and background noise all affect what we hear. OpenFault Lab explores whether a low-cost microcontroller can establish a machine's normal operating baseline and recognize changes worth investigating.

## Status

This repository starts with a project plan. Firmware, sensor wiring, hardware measurements, and detection results are not yet available. The intended development board is **NUCLEO-C5A3ZG**; board availability and the complete sensor configuration still need to be confirmed. No successful build, hardware test, or detection performance is claimed.

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
| [docs/ROADMAP.md](docs/ROADMAP.md) | Phases and the first feasibility checklist |
| [docs/VALIDATION.md](docs/VALIDATION.md) | What has and has not been verified |
| [hardware/README.md](hardware/README.md) | Planned bench hardware and wiring gates |
| [firmware/stm32c5/README.md](firmware/stm32c5/README.md) | STM32C5 firmware scope and toolchain status |
| [dataset/README.md](dataset/README.md) | Data provenance, splits, and release rules |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |

There are no build or installation commands yet. They will be added after the toolchain and first runnable implementation are verified.

## References

- [STM32Cube Innovation Challenge](https://www.elektormagazine.com/stm32cube-innovation-challenge)
- [Challenge rules](https://www.elektormagazine.com/stm32cube-terms-conditions)
- [NUCLEO-C5A3ZG product page](https://www.st.com/en/evaluation-tools/nucleo-c5a3zg.html)
- [STM32C5A3ZG product page](https://www.st.com/en/microcontrollers-microprocessors/stm32c5a3zg.html)

## License

Original project code and documentation in this repository are released under the [MIT License](LICENSE). Third-party components retain their own licenses and must be identified when added. Datasets require their own release terms; no dataset is currently included.
