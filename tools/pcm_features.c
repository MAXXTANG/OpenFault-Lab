/* SPDX-License-Identifier: MIT */
#include "openfault.h"
#include <inttypes.h>
#include <stdio.h>

static of_workspace workspace;
static unsigned char bytes[OF_WINDOW * 2U];
static int16_t pcm[OF_WINDOW];

int main(int argc, char **argv)
{
    if (argc != 2) { fprintf(stderr, "Usage: pcm_features INPUT_PCM16_LE\n"); return 2; }
    FILE *input = fopen(argv[1], "rb");
    if (!input) { perror("open PCM"); return 2; }
    uint64_t window = 0;
    size_t count;
    while ((count = fread(bytes, 1, sizeof(bytes), input)) != 0) {
        if (count != sizeof(bytes)) {
            fprintf(stderr, "Incomplete PCM window: %zu bytes (expected %zu)\n", count, sizeof(bytes));
            fclose(input); return 2;
        }
        for (size_t i = 0; i < OF_WINDOW; ++i) {
            uint32_t value = (uint32_t)bytes[2*i] | ((uint32_t)bytes[2*i+1] << 8);
            pcm[i] = (int16_t)(value < 32768U ? (int32_t)value : (int32_t)value-65536);
        }
        of_features f;
        if (!of_analyze(pcm, OF_WINDOW, OF_SAMPLE_RATE, &workspace, &f)) {
            fclose(input); return 2;
        }
        if (printf("{\"window\":%" PRIu64 ",\"sample_offset\":%" PRIu64
                   ",\"ac_rms\":%.9g,\"peak\":%.9g,\"mean\":%.9g,\"zcr\":%.9g,"
                   "\"dominant_hz\":%.9g,\"centroid_hz\":%.9g,\"clipped\":%" PRIu32 "}\n",
                   window, window*(uint64_t)OF_WINDOW, (double)f.ac_rms, (double)f.peak,
                   (double)f.mean, (double)f.zero_crossing_rate, (double)f.dominant_hz,
                   (double)f.centroid_hz, f.clipped_samples) < 0) {
            fclose(input); return 2;
        }
        ++window;
    }
    int failed = ferror(input);
    if (fclose(input) != 0 || fflush(stdout) != 0) failed = 1;
    if (!window) { fprintf(stderr, "Empty PCM input\n"); failed = 1; }
    return failed ? 2 : 0;
}
