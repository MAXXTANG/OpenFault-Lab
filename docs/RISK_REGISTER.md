# Current risks and limits

| Risk | Current response | Verification still needed |
| --- | --- | --- |
| Synthetic data mistaken for sensor results | STM32 and host emit `source=synthetic`; XIAO emits `source=microphone` | Inspect hardware boot logs |
| Noise/speed changes trigger alerts | Per-installation calibration; frozen RMS baseline with debounce; no fault labels | Session-based false-alarm testing |
| Quiet startup establishes wrong baseline | Run normally before boot, or send `r` to XIAO to recalibrate | Compare normal speeds and calibration stability |
| Audio capture overruns while processing/output runs | Small streaming frame and no filesystem/network work | Instrument overruns, timing, and USB disconnect behavior |
| ST sample oscillator or solder-bridge assumptions differ | Keep reference init unchanged and document PA2/PA3, HSE assumptions | Inspect exact board schematic/revision |
| Stack use exceeds reservation | STM32 reserves 4 KiB; static FFT workspace | Hardware stack watermark and full call-chain analysis |
| XIAO is a different platform | Shared core, explicitly separate acquisition adapter | Final competition demonstrator must use STM32C5 |
| External sensor drivers are not designed | No guessed STM32 I2S/I2C mappings | Exact sensor BOM, timing and pin-conflict review |
| ST components mistaken for MIT project code | Download dependencies separately; retain notices | License review before distributing binaries |

No public accuracy, fault-diagnosis, cross-device generalization, or remaining-life claim is supported by this increment.
