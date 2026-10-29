/* SPDX-License-Identifier: MIT */
#include "mx_system.h"
#include "mx_usart2.h"
#include "openfault.h"
#include <string.h>
static of_workspace workspace;
static of_detector detector;
static int16_t pcm[OF_WINDOW];
static char line[256];
static const int16_t wave[16] = {0,3135,5793,7568,8192,7568,5793,3135,0,-3135,-5793,-7568,-8192,-7568,-5793,-3135};
int main(void)
{
    if (mx_system_init() != SYSTEM_OK) for (;;) {}
    hal_uart_handle_t *uart = mx_usart2_uart_init();
    if (!uart) for (;;) {}
    static const char banner[] = "{\"type\":\"boot\",\"target\":\"NUCLEO-C5A3ZG\",\"mode\":\"synthetic\",\"sensors_connected\":false}\n";
    if (HAL_UART_Transmit(uart, (const uint8_t *)banner, sizeof(banner)-1U, 100U) != HAL_OK)
        for (;;) {}
    of_detector_reset(&detector);
    uint32_t seq = 0;
    for (;;) {
        /* Generated signal only: normal amplitude, then an amplitude step. */
        unsigned scale = (seq % 128U >= 64U) ? 2U : 1U;
        for (size_t i = 0; i < OF_WINDOW; ++i) pcm[i] = (int16_t)(wave[i % 16U] * (int)scale);
        of_features f; of_detection d;
        if (!of_analyze(pcm, OF_WINDOW, OF_SAMPLE_RATE, &workspace, &f) ||
            !of_detector_update(&detector, f.ac_rms, &d)) for (;;) {}
        int count = of_format_event(line, sizeof(line), seq++, HAL_GetTick(), 0, &f, &d);
        if (!count || HAL_UART_Transmit(uart, (const uint8_t *)line, (uint32_t)count, 100U) != HAL_OK)
            for (;;) {}
        HAL_Delay(64U); /* Demo pacing; not an audio sampling clock. */
    }
}
