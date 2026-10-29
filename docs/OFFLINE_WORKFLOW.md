# Offline experiments without flashing a device

This workflow runs entirely on a computer. It does not upload firmware, access a microphone, or start recording audio. Requirements: CMake, a C11 compiler, Ninja, and Python **3.10 or later**. The host tools use only the Python standard library.

## 1. Build and verify

From the repository root:

```sh
cmake -S . -B build/host -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/host
ctest --test-dir build/host --output-on-failure
```

`pcm_features` calls the exact `of_analyze` C implementation used by both firmware targets. It expects headerless, little-endian PCM16 mono at 16 kHz and rejects empty or incomplete windows. The Python workflow checks WAV headers and streams complete PCM windows through that executable. This avoids silently changing the feature definition in a separate Python DSP implementation.

## 2. Run the synthetic demonstration

```sh
python3 tools/offline.py demo --out outputs/demo_01
```

Outputs:

- `synthetic_inputs/manifest.json` and five deterministic, explicitly synthetic WAV sessions.
- `evaluation/features/*.jsonl`: full-precision C features for each window.
- `evaluation/result.json`: training parameters, input PCM hashes, predictions, confusion counts, metrics and limitations.
- `evaluation/report.html`: a self-contained report with no external assets or raw audio embedded.

Open `outputs/demo_01/evaluation/report.html` in a browser. The demo has two normal training sessions and three held-out test sessions. Its RMS-only detector detects an amplitude step but misses an equal-amplitude frequency change. The report exposes this known limitation rather than presenting the demo as a successful fault classifier. All numbers are synthetic software checks, not hardware performance.

The output directory must be new. Existing outputs are never overwritten. Failed evaluations may leave intermediate feature files; use a new directory for a corrected run.

## 3. Evaluate controlled recordings later

Use [the manifest template](../dataset/manifest.example.json) as a starting point. No real recording is included in this repository. Place the manifest beside its authorized WAV files, then run:

```sh
python3 tools/offline.py evaluate \
  --manifest dataset/raw/experiment_01/manifest.json \
  --out outputs/experiment_01
```

WAV input must be uncompressed PCM16, mono, 16 kHz, between one complete 1024-sample window and one hour long. Resampling, channel mixing, or gain normalization are intentionally not implicit. If a recording has an incomplete final window, either trim it deliberately or add `"tail_policy": "drop"` to that session; the report records how many samples were dropped.

Before using measured recordings, set `provenance` to `measured` and document the actual device alias, speed, mounting, sensor position, background conditions, permissions, software revision and dataset license separately. Reading an existing WAV is an explicit offline experiment; ordinary firmware monitoring and the event logger do not retain raw audio.

## Split and annotation rules

- A session is one whole recording. Give it a unique anonymous `session_id` and one split; never divide overlapping windows from one session between training and test.
- `split_unit=session` fits one normal baseline per device. Every test device needs separate normal training sessions.
- `split_unit=device` requires disjoint train/test devices and fits an explicitly pooled training baseline. This is a different experiment, not proof of generalization.
- Training sessions must have empty `anomalous_intervals`. At least 32 normal training windows are required for each fitted baseline.
- Annotation intervals are **zero-based window indices, half-open `[start, end)`**. They must be ordered, nonoverlapping and within the recording. With 1024/16000 samples per window, `[32, 64)` covers 2.048–4.096 seconds. Keep the original condition notes supporting each annotation.
- Duplicate session IDs, repeated paths, paths outside the manifest folder, and identical used PCM payloads are rejected. Edited or overlapping excerpts with different content hashes still require a provenance audit.

## How scores and metrics are calculated

The offline baseline uses every normal training window's AC RMS. It freezes the sample mean and standard deviation before reading test scores. The standard-deviation floor is 0.005 full scale, the fixed threshold is 6, and three consecutive high windows are required. Test data never update the model or tune the threshold. Consecutive state resets between test sessions.

The host fit uses Python double arithmetic and all supplied training windows. Firmware uses float arithmetic and its first 32 calibration windows, so this is the same rule with an explicit training protocol, not a claim of identical runtime scores.

- Precision, recall and F1 use **window** confusion counts. Undefined denominators are `null` in JSON and `undefined` in HTML.
- A false-alert episode is a rising edge of predicted anomaly while the annotation is normal, reset at session boundaries. A prediction crossing into a normal interval counts there. Divide episodes by observed normal exposure, then multiply by 3600 for false alerts/hour. Short exposure cannot establish a reliable long-term rate.
- Each annotated variation interval contributes one delay if detected: the **end** of its first predicted-anomaly window minus the annotated onset. Undetected intervals remain in the interval denominator and have no fabricated latency. This nominal sample-timeline delay excludes processing, USB/network I/O and scheduling; it is not measured inference latency.
- RMS scoring ignores spectral features today. Full-precision dominant frequency, centroid, peak and clipping remain available in feature JSONL for later comparisons.

## Event-only session logging

For post-flash use later, or for offline replay now, see [TELEMETRY.md](TELEMETRY.md). Those summaries are not WAV data and are not accepted by the waveform evaluation manifest. This keeps host arrival timestamps separate from PCM sample time and avoids quietly treating a reboot's calibration epoch as a new training dataset.
