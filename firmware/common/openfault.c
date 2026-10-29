/* SPDX-License-Identifier: MIT */
#include "openfault.h"
#include <math.h>
#include <string.h>
#define OF_PI 3.14159265358979323846f

void of_detector_reset(of_detector *d) { if (d) memset(d, 0, sizeof(*d)); }

int of_analyze(const int16_t *pcm, size_t n, uint32_t rate,
               of_workspace *w, of_features *out)
{
    if (!pcm || !w || !out || n != OF_WINDOW || !rate) return 0;
    of_features f = {0};
    float sum = 0.0f, squares = 0.0f;
    unsigned crossings = 0;
    for (size_t i = 0; i < n; ++i) {
        float x = (float)pcm[i] / 32768.0f;
        sum += x;
        if (fabsf(x) > f.peak) f.peak = fabsf(x);
        if (pcm[i] == INT16_MIN || pcm[i] == INT16_MAX) ++f.clipped_samples;
    }
    f.mean = sum / (float)n;
    for (size_t i = 0; i < n; ++i) {
        float x = (float)pcm[i] / 32768.0f - f.mean;
        squares += x * x;
        if (i && ((x >= 0.0f) != (((float)pcm[i-1] / 32768.0f - f.mean) >= 0.0f)))
            ++crossings;
        w->real[i] = x * (0.5f - 0.5f * cosf(2.0f * OF_PI * (float)i / (float)(n-1)));
        w->imag[i] = 0.0f;
    }
    f.ac_rms = sqrtf(squares / (float)n);
    f.zero_crossing_rate = (float)crossings / (float)(n-1);
    /* In-place radix-2 complex FFT, with a real, Hann-windowed input. */
    for (size_t i = 1, j = 0; i < n; ++i) {
        size_t bit = n >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) {
            float t = w->real[i]; w->real[i] = w->real[j]; w->real[j] = t;
        }
    }
    for (size_t len = 2; len <= n; len <<= 1) {
        float angle = -2.0f * OF_PI / (float)len;
        float step_r = cosf(angle), step_i = sinf(angle);
        for (size_t start = 0; start < n; start += len) {
            float wr = 1.0f, wi = 0.0f;
            for (size_t j = 0; j < len / 2; ++j) {
                size_t a = start + j, b = a + len / 2;
                float vr = w->real[b]*wr - w->imag[b]*wi;
                float vi = w->real[b]*wi + w->imag[b]*wr;
                float ur = w->real[a], ui = w->imag[a];
                w->real[a] = ur+vr; w->imag[a] = ui+vi;
                w->real[b] = ur-vr; w->imag[b] = ui-vi;
                float next = wr*step_r - wi*step_i;
                wi = wr*step_i + wi*step_r; wr = next;
            }
        }
    }
    float total = 0.0f, weighted = 0.0f, maximum = 0.0f;
    for (size_t k = 1; k <= n/2; ++k) {
        float power = w->real[k]*w->real[k] + w->imag[k]*w->imag[k];
        float hz = (float)k * (float)rate / (float)n;
        total += power; weighted += power * hz;
        if (power > maximum) { maximum = power; f.dominant_hz = hz; }
    }
    if (total > 1.0e-12f) f.centroid_hz = weighted / total;
    else f.dominant_hz = 0.0f;
    *out = f;
    return 1;
}

int of_detector_update(of_detector *d, float rms, of_detection *out)
{
    if (!d || !out || !isfinite(rms) || rms < 0.0f || rms > 1.0f) return 0;
    of_detection result = {OF_CALIBRATING, 0.0f};
    if (d->count < OF_CALIBRATION_WINDOWS) {
        ++d->count;
        float delta = rms - d->mean;
        d->mean += delta / (float)d->count;
        d->m2 += delta * (rms - d->mean);
    } else {
        float stddev = sqrtf(fmaxf(0.0f, d->m2 / (float)(d->count-1)));
        result.score = fabsf(rms-d->mean) / fmaxf(stddev, 0.005f);
        if (result.score >= 6.0f) {
            if (d->consecutive < 3U) ++d->consecutive;
        } else d->consecutive = 0;
        result.state = d->consecutive >= 3U ? OF_ANOMALY : OF_NORMAL;
    }
    *out = result;
    return 1;
}
