# Roadmap

All items below are planned work, not completed results. The internal completion target is January 28, 2027; hardware availability may require revising the schedule.

## P0: Feasibility and design review — next

- [ ] Confirm board availability and the exact NUCLEO-C5A3ZG revision.
- [ ] Record official MCU, board, schematic, errata, STM32Cube, and HAL documentation versions.
- [ ] Verify I2S microphone compatibility and an ADC fallback, including actual pins and timing.
- [ ] Choose an accelerometer and verify its interface, bandwidth, sample rate, and mounting.
- [ ] Verify pin conflicts, DMA routing, time alignment, Ethernet resources, and power requirements.
- [ ] Calculate streaming-buffer, FFT, model, stack, and network RAM/Flash budgets.
- [ ] Define the minimum BOM and guarded low-voltage bench fixture.
- [ ] Write architecture, technical research, implementation, risk, and test plans with verified facts separated from assumptions.

Completion gate: a documented, reviewable design with unresolved hardware assumptions clearly listed. No unverified pin mapping or substantial firmware generation before this review.

## P1: Host baseline and data — planned

Create session-based data capture and feature extraction; establish a transparent baseline. Use labeled synthetic signals only for software checks. Compare normal operation and controlled variations using recordings from separate sessions or devices.

## P2: STM32C5 implementation — planned

Verify the official toolchain and a reproducible build/flash path. Bring up UART, microphone acquisition, the accelerometer, and DSP independently before integration. Measure resources before considering TinyML. Complete UART output first, then local Ethernet summaries; acquisition must continue if the network is unavailable.

## P3: Evaluation and publication — planned

Publish the actual BOM and wiring, a reproducible test procedure, measured baseline/model comparisons, known limitations, and an English build tutorial and demo. Prepare final Elektor Labs materials before the internal deadline. Application submission, board selection, and final contest submission are separate milestones.
