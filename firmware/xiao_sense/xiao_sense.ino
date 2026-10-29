// SPDX-License-Identifier: MIT
#include <Arduino.h>
#include <ESP_I2S.h>
#include "openfault.h"
static I2SClass mic;
static of_workspace workspace;
static of_detector detector;
static int16_t pcm[OF_WINDOW];
static char line[256];
static uint32_t sequence = 0;
static void stop(const char *message) {
  Serial.println(message);
  for (;;) delay(1000);
}
void setup() {
  Serial.begin(115200);
  uint32_t start = millis();
  while (!Serial && (uint32_t)(millis()-start) < 5000U) delay(10);
  mic.setPinsPdmRx(42, 41); // Seeed's documented PDM clock/data pins.
  if (!mic.begin(I2S_MODE_PDM_RX, OF_SAMPLE_RATE, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO))
    stop("{\"type\":\"error\",\"error\":\"pdm_init\"}");
  of_detector_reset(&detector);
  Serial.println("{\"type\":\"boot\",\"target\":\"XIAO_ESP32S3_Sense\",\"mode\":\"microphone\",\"sample_rate\":16000,\"window\":1024,\"raw_audio_storage\":false}");
}
void loop() {
  while (Serial.available()) {
    if (Serial.read() == 'r') {
      of_detector_reset(&detector);
      Serial.println("{\"type\":\"calibration_reset\"}");
    }
  }
  size_t filled = 0;
  while (filled < sizeof(pcm)) {
    size_t n = mic.readBytes((char *)pcm + filled, sizeof(pcm)-filled);
    if (!n) stop("{\"type\":\"error\",\"error\":\"pdm_read_timeout\"}");
    filled += n;
  }
  of_features f; of_detection d;
  if (!of_analyze(pcm, OF_WINDOW, OF_SAMPLE_RATE, &workspace, &f) ||
      !of_detector_update(&detector, f.ac_rms, &d))
    stop("{\"type\":\"error\",\"error\":\"processing\"}");
  int n = of_format_event(line, sizeof(line), sequence++, millis(), 1, &f, &d);
  if (!n) stop("{\"type\":\"error\",\"error\":\"telemetry\"}");
  if (Serial.write((const uint8_t *)line, (size_t)n) != (size_t)n)
    stop("{\"type\":\"error\",\"error\":\"serial_short_write\"}");
  // DMA overruns and processing deadlines still require on-device instrumentation.
}
