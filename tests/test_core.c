/* SPDX-License-Identifier: MIT */
#include "openfault.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "line %d: %s\n", __LINE__, #x); exit(1); } } while (0)
#define NEAR(a,b,t) CHECK(fabsf((a)-(b)) < (t))
static of_workspace w;
static int16_t pcm[OF_WINDOW];
static void test_signals(void) {
    of_features f;
    CHECK(of_analyze(pcm, OF_WINDOW, OF_SAMPLE_RATE, &w, &f));
    CHECK(f.ac_rms == 0 && f.dominant_hz == 0 && f.centroid_hz == 0);
    for (size_t i = 0; i < OF_WINDOW; ++i) pcm[i] = 8192;
    CHECK(of_analyze(pcm, OF_WINDOW, OF_SAMPLE_RATE, &w, &f));
    NEAR(f.mean, 0.25f, 0.00001f); CHECK(f.ac_rms == 0 && f.dominant_hz == 0);
    for (size_t i = 0; i < OF_WINDOW; ++i)
        pcm[i] = (int16_t)(16384.0f*sinf(6.28318530718f*64.0f*(float)i/OF_WINDOW));
    CHECK(of_analyze(pcm, OF_WINDOW, OF_SAMPLE_RATE, &w, &f));
    NEAR(f.ac_rms, 0.353553f, 0.0001f); NEAR(f.dominant_hz, 1000.0f, 0.01f);
    NEAR(f.centroid_hz, 1000.0f, 1.0f); NEAR(f.zero_crossing_rate, 0.125f, 0.003f);
    for (size_t i = 0; i < OF_WINDOW; ++i) {
        float t = 6.28318530718f*(float)i/OF_WINDOW;
        pcm[i] = (int16_t)(16384.0f*sinf(64.0f*t) + 8192.0f*sinf(128.0f*t));
    }
    CHECK(of_analyze(pcm, OF_WINDOW, OF_SAMPLE_RATE, &w, &f));
    NEAR(f.dominant_hz, 1000.0f, 0.01f); NEAR(f.centroid_hz, 1200.0f, 1.0f);
    for (size_t i = 0; i < OF_WINDOW; ++i) pcm[i] = i%2 ? INT16_MIN : INT16_MAX;
    CHECK(of_analyze(pcm, OF_WINDOW, OF_SAMPLE_RATE, &w, &f));
    CHECK(f.clipped_samples == OF_WINDOW); NEAR(f.dominant_hz, 8000.0f, 0.01f);
    CHECK(!of_analyze(NULL, OF_WINDOW, OF_SAMPLE_RATE, &w, &f));
    CHECK(!of_analyze(pcm, OF_WINDOW-1, OF_SAMPLE_RATE, &w, &f));
    CHECK(!of_analyze(pcm, OF_WINDOW, 0, &w, &f));
    CHECK(!of_analyze(pcm, OF_WINDOW, OF_SAMPLE_RATE, NULL, &f));
}
static void test_baseline(void) {
    of_detector d; of_detection event; of_detector_reset(&d);
    for (unsigned i = 0; i < OF_CALIBRATION_WINDOWS; ++i) {
        CHECK(of_detector_update(&d, 0.2f, &event)); CHECK(event.state == OF_CALIBRATING);
    }
    CHECK(of_detector_update(&d, 0.2f, &event)); CHECK(event.state == OF_NORMAL);
    CHECK(of_detector_update(&d, 0.4f, &event)); CHECK(event.state == OF_NORMAL);
    CHECK(of_detector_update(&d, 0.2f, &event)); CHECK(d.consecutive == 0);
    for (unsigned i = 0; i < 3; ++i) CHECK(of_detector_update(&d, 0.4f, &event));
    CHECK(event.state == OF_ANOMALY); NEAR(event.score, 40.0f, 0.001f);
    NEAR(d.mean, 0.2f, 0.00001f); // Anomaly must not pollute the frozen baseline.
    CHECK(of_detector_update(&d, 0.2f, &event)); CHECK(event.state == OF_NORMAL);
    of_detector variable; of_detector_reset(&variable);
    for (unsigned i = 0; i < OF_CALIBRATION_WINDOWS; ++i)
        CHECK(of_detector_update(&variable, i%2 ? 0.25f : 0.15f, &event));
    CHECK(of_detector_update(&variable, 0.4f, &event));
    NEAR(event.score, 3.937f, 0.01f); CHECK(event.state == OF_NORMAL);
    uint32_t count = d.count;
    CHECK(!of_detector_update(&d, NAN, &event)); CHECK(d.count == count);
    CHECK(!of_detector_update(&d, INFINITY, &event));
    CHECK(!of_detector_update(&d, -0.1f, &event));
    of_detector_reset(&d); CHECK(d.count == 0 && d.consecutive == 0);
    CHECK(of_detector_update(&d, 0.2f, &event)); CHECK(event.state == OF_CALIBRATING);
}
static void test_telemetry(void) {
    char text[256], small[8]; of_features f = {0}; of_detection d = {OF_NORMAL, 2.0f};
    f.ac_rms = 0.25f; f.dominant_hz = 1000;
    int n = of_format_event(text, sizeof(text), UINT32_MAX, UINT32_MAX, 1, &f, &d);
    CHECK(n > 0 && (size_t)n == strlen(text)); CHECK(text[n-1] == '\n');
    CHECK(strstr(text, "\"source\":\"microphone\"")); CHECK(strstr(text, "4294967295"));
    CHECK(!of_format_event(small, sizeof(small), 0, 0, 0, &f, &d)); CHECK(small[0] == '\0');
    CHECK(!of_format_event(text, sizeof(text), 0, 0, 2, &f, &d));
    f.ac_rms = NAN; CHECK(!of_format_event(text, sizeof(text), 0, 0, 0, &f, &d));
}
int main(void) {
    test_signals(); test_baseline(); test_telemetry();
    puts("PASS: signal features, FFT, calibration, debounce, invalid input, telemetry bounds");
    return 0;
}
