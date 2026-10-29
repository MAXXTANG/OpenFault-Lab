# Roadmap

The first implementation increment is now present: shared C core, native tests, a XIAO microphone sketch, and an STM32 UART synthetic target. Remaining items below are planned work, not completed results. The internal completion target is January 28, 2027; hardware availability may require revising the schedule.

## P0: Feasibility and design review — partial

- [ ] Confirm board availability and the exact NUCLEO-C5A3ZG revision.
- [x] Pin official STM32CubeC5/HAL2 sources for the UART increment.
- [ ] Complete board schematic, errata, and external-sensor documentation review.
- [ ] Verify I2S microphone compatibility and an ADC fallback, including actual pins and timing.
- [ ] Choose an accelerometer and verify its interface, bandwidth, sample rate, and mounting.
- [ ] Verify pin conflicts, DMA routing, time alignment, Ethernet resources, and power requirements.
- [x] Estimate PCM/FFT streaming memory and link the UART synthetic target.
- [ ] Measure stack high-water and budget future DMA, model, and network memory.
- [ ] Define the minimum BOM and guarded low-voltage bench fixture.
- [x] Write the first architecture, technical research, implementation, risk, and test plans.
- [ ] Resolve remaining external-sensor assumptions before integrating STM32 acquisition.

Completion gate: a documented, reviewable design with unresolved hardware assumptions clearly listed. No unverified pin mapping or substantial firmware generation before this review.

## P1: Host baseline and data — started

The no-flash tooling is implemented:

- [x] Extract PCM16 WAV features through the shared C implementation.
- [x] Validate session/device split rules, normal-only fitting, exact duplicate PCM and file provenance boundaries.
- [x] Run a deterministic synthetic experiment that exposes both detectable amplitude changes and missed frequency changes.
- [x] Report window confusion counts, precision/recall/F1, false alert episodes/hour and nominal detection delay.
- [x] Record feature-only JSONL sessions; check resets, source, gaps and counter wraps.
- [x] Generate a self-contained HTML report and test the serial adapter with a virtual terminal.
- [ ] Acquire authorized, labeled real-machine sessions and report measured results.
- [ ] Instrument device timing, DMA continuity and memory high-water on hardware.

## P2: STM32C5 implementation — UART target started

Verify the official toolchain and a reproducible build/flash path. Bring up UART, microphone acquisition, the accelerometer, and DSP independently before integration. Measure resources before considering TinyML. Complete UART output first, then local Ethernet summaries; acquisition must continue if the network is unavailable.

## P3: Evaluation and publication — planned

Publish the actual BOM and wiring, a reproducible test procedure, measured baseline/model comparisons, known limitations, and an English build tutorial and demo. Prepare final Elektor Labs materials before the internal deadline. Application submission, board selection, and final contest submission are separate milestones.
