/* SPDX-License-Identifier: MIT */
#include "openfault.h"
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
int of_format_event(char *b, size_t cap, uint32_t seq, uint32_t ms, unsigned source,
                    const of_features *f, const of_detection *d)
{
    if (!b || !cap) return 0;
    b[0] = '\0';
    if (!f || !d || source > 1U || (unsigned)d->state > (unsigned)OF_ANOMALY ||
        !isfinite(f->ac_rms) || f->ac_rms < 0 || f->ac_rms > 1 ||
        !isfinite(f->dominant_hz) || f->dominant_hz < 0 || f->dominant_hz > 8000 ||
        !isfinite(d->score) || d->score < 0 || d->score > 1000000) return 0;
    const char *states[] = {"calibrating", "normal", "anomaly"};
    int n = snprintf(b, cap,
        "{\"v\":1,\"source\":\"%s\",\"seq\":%" PRIu32 ",\"uptime_ms\":%" PRIu32
        ",\"state\":\"%s\",\"rms_milli\":%" PRIu32 ",\"dominant_hz\":%" PRIu32
        ",\"score_milli\":%" PRIu32 ",\"clipped\":%" PRIu32 "}\n",
        source ? "microphone" : "synthetic", seq, ms, states[d->state],
        (uint32_t)(f->ac_rms*1000.0f), (uint32_t)f->dominant_hz,
        (uint32_t)(d->score*1000.0f), f->clipped_samples);
    if (n < 0 || (size_t)n >= cap) { b[0] = '\0'; return 0; }
    return n;
}
