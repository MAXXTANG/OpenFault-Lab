/* SPDX-License-Identifier: MIT */
#include "openfault.h"
#include <math.h>
#include <stdio.h>
static of_workspace workspace;
static int16_t pcm[OF_WINDOW];
int main(void) {
    of_detector d; of_detector_reset(&d);
    for (uint32_t seq = 0; seq < 80U; ++seq) {
        float amplitude = seq < 48U ? 0.25f : 0.5f;
        for (size_t i = 0; i < OF_WINDOW; ++i)
            pcm[i] = (int16_t)(32767.0f*amplitude*sinf(6.28318530718f*64.0f*(float)i/(float)OF_WINDOW));
        of_features f; of_detection event; char line[256];
        if (!of_analyze(pcm, OF_WINDOW, OF_SAMPLE_RATE, &workspace, &f) ||
            !of_detector_update(&d, f.ac_rms, &event) ||
            !of_format_event(line, sizeof(line), seq, seq*64U, 0, &f, &event)) return 1;
        fputs(line, stdout);
    }
    return 0;
}
