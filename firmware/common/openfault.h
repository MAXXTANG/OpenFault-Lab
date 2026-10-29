/* SPDX-License-Identifier: MIT */
#ifndef OPENFAULT_H
#define OPENFAULT_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define OF_WINDOW 1024U
#define OF_SAMPLE_RATE 16000U
#define OF_CALIBRATION_WINDOWS 32U
/* One workspace per task. Not reentrant; no allocation or raw-audio retention. */
typedef struct { float real[OF_WINDOW], imag[OF_WINDOW]; } of_workspace;
typedef struct {
    float mean, ac_rms, peak, zero_crossing_rate, dominant_hz, centroid_hz;
    uint32_t clipped_samples;
} of_features;
typedef enum { OF_CALIBRATING, OF_NORMAL, OF_ANOMALY } of_state;
typedef struct { uint32_t count, consecutive; float mean, m2; } of_detector;
typedef struct { of_state state; float score; } of_detection;
void of_detector_reset(of_detector *detector);
/* PCM is signed 16-bit mono. Requires exactly OF_WINDOW samples. */
int of_analyze(const int16_t *pcm, size_t count, uint32_t sample_rate,
               of_workspace *workspace, of_features *features);
/* Frozen RMS baseline. Scores use a full-scale standard-deviation floor of 0.005. */
int of_detector_update(of_detector *detector, float ac_rms, of_detection *out);
/* source: 0=synthetic, 1=microphone. Returns 0 on truncation or invalid data. */
int of_format_event(char *buffer, size_t capacity, uint32_t sequence,
                    uint32_t uptime_ms, unsigned source,
                    const of_features *features, const of_detection *detection);
#ifdef __cplusplus
}
#endif
#endif
