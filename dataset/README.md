# Dataset

No dataset is currently published. There are no measured detection results.

Future recordings must come from controlled, authorized bench tests. Keep unreviewed recordings under `dataset/raw/`, which is ignored by Git. Do not include speech or identifiable background audio in a public release.

Record device aliases, recording session, sample rates, sensor position, operating speed, mounting, background conditions, software version, and normal/controlled-variation labels. Split training and test sets by session or device before generating windows. Synthetic waveforms must be labeled as synthetic.

The repository MIT License does not grant a license to datasets. Each dataset release must include provenance, permissions, a separately chosen license, and its own manifest. Normal device monitoring will not retain or upload raw audio.

## Manifest and offline evaluation

[manifest.example.json](manifest.example.json) is a template, not a measured dataset. Its example WAV paths do not exist in this repository. Replace the paths and annotations with authorized controlled sessions, and set provenance truthfully. Use [the offline workflow](../docs/OFFLINE_WORKFLOW.md) to extract shared C features and evaluate held-out sessions. Synthetic demo WAVs are generated only under ignored local output folders.
