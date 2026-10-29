"""Host pipeline tests use synthetic inputs and a virtual serial terminal only (MIT)."""
from pathlib import Path
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
EXTRACTOR = Path(sys.argv.pop(1)).resolve()
sys.path.insert(0, str(ROOT/"host"))
sys.path.insert(0, str(ROOT/"tools"))
from openfault.pipeline import evaluate, load_manifest, make_demo, metrics
from openfault.events import record
from openfault.report import render_report
from record_events import serial_lines


def event(seq=0, tick=0, **kwargs):
    result = {"v": 1, "source": "synthetic", "seq": seq, "uptime_ms": tick,
              "state": "normal", "rms_milli": 200, "dominant_hz": 1000,
              "score_milli": 0, "clipped": 0}
    result.update(kwargs)
    return result


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.TemporaryDirectory()
        cls.fixture = Path(cls.base.name)/"fixtures"
        make_demo(cls.fixture)

    @classmethod
    def tearDownClass(cls):
        cls.base.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = self.root/"inputs"
        shutil.copytree(self.fixture, self.data)
        self.manifest = self.data/"manifest.json"

    def tearDown(self):
        self.temp.cleanup()

    def mutate(self, change):
        doc = json.loads(self.manifest.read_text())
        change(doc)
        self.manifest.write_text(json.dumps(doc))

    def run_evaluation(self, name="result"):
        return evaluate(self.manifest, EXTRACTOR, self.root/name)

    def test_complete_pipeline_and_known_limitation(self):
        result = self.run_evaluation()
        m = result["metrics"]
        self.assertEqual(m["confusion"], {"tp": 30, "fp": 0, "tn": 224, "fn": 34})
        self.assertEqual(m["window_detection_delays_ms"], [192.0])
        self.assertEqual((m["detected_intervals"], m["total_intervals"]), (1, 2))
        self.assertEqual(m["false_alerts_per_hour"], 0)
        self.assertAlmostEqual(m["f1"], 60/94)
        self.assertEqual(result["baseline"]["models"]["synthetic_fan"]["windows"], 192)
        self.assertIn("SYNTHETIC SOFTWARE CHECK", (self.root/"result/report.html").read_text())
        self.assertFalse(list((self.root/"result").rglob("*.wav")))
        frequency = result["test_sessions"][2]
        self.assertEqual(max(frequency["dominant_hz"]), 2000)
        self.assertEqual(sum(frequency["predictions"]), 0)
        with self.assertRaises(FileExistsError):
            self.run_evaluation()

    def test_no_test_data_fitting(self):
        before = self.run_evaluation("before")["baseline"]
        target = self.data/"test_normal.wav"
        with wave.open(str(target), "rb") as stream:
            params, payload = stream.getparams(), stream.readframes(stream.getnframes())
        samples = struct.unpack("<"+"h"*(len(payload)//2), payload)
        with wave.open(str(target), "wb") as stream:
            stream.setparams(params)
            stream.writeframes(struct.pack("<"+"h"*len(samples), *[s//2 for s in samples]))
        self.assertEqual(before, self.run_evaluation("after")["baseline"])

    def test_content_duplicate_rejected(self):
        shutil.copyfile(self.data/"train_a.wav", self.data/"test_normal.wav")
        with self.assertRaisesRegex(ValueError, "Identical PCM"):
            self.run_evaluation()
        self.assertFalse((self.root/"result/result.json").exists())

    def test_session_device_and_path_leakage_rejected(self):
        original = self.manifest.read_text()
        mutations = [
            lambda d: d["sessions"][2].update(session_id="train_a"),
            lambda d: d["sessions"][2].update(wav="train_a.wav"),
            lambda d: d["sessions"][2].update(wav="../../outside.wav"),
            lambda d: d.update(split_unit="device"),
            lambda d: d["sessions"][2].update(device_id="unseen_device"),
            lambda d: d["sessions"][0].update(anomalous_intervals=[[0, 3]]),
            lambda d: d.update(provenance="unknown"),
        ]
        for mutation in mutations:
            self.manifest.write_text(original)
            self.mutate(mutation)
            with self.assertRaises(ValueError):
                load_manifest(self.manifest)

    def test_device_split_uses_explicit_pooled_model(self):
        def change(doc):
            doc["split_unit"] = "device"
            for session in doc["sessions"]:
                if session["split"] == "test":
                    session["device_id"] = "heldout_device"
        self.mutate(change)
        result = self.run_evaluation()
        self.assertEqual(result["baseline"]["scope"], "pooled")
        self.assertEqual(set(result["baseline"]["models"]), {"pooled"})

    def test_tail_requires_explicit_drop(self):
        target = self.data/"test_normal.wav"
        with wave.open(str(target), "rb") as stream:
            params, payload = stream.getparams(), stream.readframes(stream.getnframes())
        with wave.open(str(target), "wb") as stream:
            stream.setparams(params)
            stream.writeframes(payload+b"\x00\x00")
        with self.assertRaisesRegex(ValueError, "Partial final"):
            self.run_evaluation("strict")
        self.mutate(lambda d: d["sessions"][2].update(tail_policy="drop"))
        result = self.run_evaluation("drop")
        self.assertEqual(result["sessions"][2]["dropped_tail_samples"], 1)

    def test_bad_format_and_annotation_rejected(self):
        self.mutate(lambda d: d["sessions"][3].update(anomalous_intervals=[[30, 50], [40, 60]]))
        with self.assertRaisesRegex(ValueError, "nonoverlapping"):
            self.run_evaluation("bad_interval")
        with wave.open(str(self.data/"train_a.wav"), "wb") as stream:
            stream.setparams((2, 2, 8000, 0, "NONE", "not compressed"))
            stream.writeframes(b"\x00"*8192)
        with self.assertRaisesRegex(ValueError, "PCM16 mono"):
            self.run_evaluation("bad_format")

    def test_c_reader_little_endian_and_incomplete_frames(self):
        pcm = self.root/"tone.pcm"
        pcm.write_bytes(struct.pack("<hh", -32768, 32767)*512)
        proc = subprocess.run([str(EXTRACTOR), str(pcm)], capture_output=True, text=True, check=True)
        row = json.loads(proc.stdout)
        self.assertEqual(row["clipped"], 1024)
        self.assertAlmostEqual(row["mean"], -1/65536, places=8)
        self.assertEqual(row["dominant_hz"], 8000)
        for payload in (b"", b"\x01", b"\x00"*2047):
            pcm.write_bytes(payload)
            self.assertNotEqual(subprocess.run([str(EXTRACTOR), str(pcm)], capture_output=True).returncode, 0)

    def test_malformed_wav_rejected_cleanly(self):
        (self.data/"train_a.wav").write_bytes(b"not-a-wave")
        with self.assertRaisesRegex(ValueError, "WAV header"):
            self.run_evaluation()

    def test_report_escapes_untrusted_text(self):
        self.mutate(lambda d: d["sessions"][2].update(condition='<script>alert("x")</script>'))
        report = render_report(self.run_evaluation())
        self.assertNotIn("<script>", report)
        self.assertIn("&lt;script&gt;", report)


class MetricTests(unittest.TestCase):
    def test_false_alert_episodes_and_nominal_delay(self):
        result = metrics([{"labels": [0, 0, 0, 1, 1, 1, 0, 0],
                           "predictions": [0, 1, 1, 1, 1, 0, 1, 0],
                           "anomalous_intervals": [[3, 6]]}])
        self.assertEqual(result["confusion"], {"tp": 2, "fp": 3, "tn": 2, "fn": 1})
        self.assertEqual(result["false_alert_episodes"], 2)
        self.assertAlmostEqual(result["normal_exposure_seconds"], 0.32)
        self.assertAlmostEqual(result["false_alerts_per_hour"], 22500)
        self.assertEqual(result["window_detection_delays_ms"], [64.0])

    def test_undefined_metrics_and_session_boundaries(self):
        row = {"labels": [0, 0], "predictions": [1, 1], "anomalous_intervals": []}
        self.assertEqual(metrics([row, row])["false_alert_episodes"], 2)
        empty = metrics([dict(row, predictions=[0, 0])])
        self.assertIsNone(empty["precision"])
        self.assertIsNone(empty["recall"])
        self.assertIsNone(empty["f1"])
        self.assertIsNone(empty["mean_window_detection_delay_ms"])
        no_normal = metrics([{"labels": [1], "predictions": [1], "anomalous_intervals": [[0, 1]]}])
        self.assertIsNone(no_normal["false_alerts_per_hour"])


class EventTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def capture(self, events, name="capture"):
        return record([json.dumps(item) for item in events], self.root/name,
                      "session_1", "device_1", "synthetic")

    def test_wrap_gaps_and_boot_epoch(self):
        events = [event(2**32-1, 2**32-32), event(0, 32), event(2, 96),
                  {"type": "calibration_reset"},
                  {"type": "boot", "target": "NUCLEO-C5A3ZG", "mode": "synthetic", "sensors_connected": False},
                  event(0, 0)]
        summary = self.capture(events)
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["feature_events"], 4)
        self.assertEqual(summary["missing_sequence_events"], 1)
        self.assertEqual(summary["sequence_wraps"], 1)
        self.assertEqual(summary["uptime_wraps"], 1)
        self.assertEqual(summary["boot_events"], 1)
        self.assertEqual(summary["calibration_resets"], 1)

    def test_invalid_events_preserve_valid_prefix_only(self):
        bad_events = [event(seq=0), event(seq=2, source="microphone"), event(seq=2, rms_milli=True),
                      event(seq=2, rms_milli=-1), event(seq=2, pcm=[1, 2, 3]), event(seq=2, score_milli=float("nan")),
                      event(seq=2, uptime_ms=2**32-1)]
        for i, invalid in enumerate(bad_events):
            with self.assertRaises(ValueError):
                self.capture([event(0, 64), invalid], f"invalid_{i}")
            summary = json.loads((self.root/f"invalid_{i}/session.json").read_text())
            self.assertFalse(summary["complete"])
            self.assertEqual(len((self.root/f"invalid_{i}/events.jsonl").read_text().splitlines()), 1)

    def test_error_and_empty_stream(self):
        with self.assertRaisesRegex(ValueError, "Device reported"):
            self.capture([event(), {"type": "error", "error": "pdm_read_timeout"}])
        with self.assertRaisesRegex(ValueError, "No feature"):
            self.capture([], "empty")
        for i, line in enumerate(["not-json", "x"*4097]):
            with self.assertRaises(ValueError):
                record([line], self.root/f"bad_{i}", "s", "d", "synthetic")

    def test_cli_replay(self):
        raw = self.root/"input.jsonl"
        raw.write_text("\n".join(json.dumps(event(i, i*64)) for i in range(4))+"\n")
        subprocess.run([sys.executable, str(ROOT/"tools/record_events.py"), "--input", str(raw),
                        "--out", str(self.root/"cli"), "--session-id", "demo", "--device-id", "fake",
                        "--source", "synthetic"], capture_output=True, check=True)
        self.assertEqual(json.loads((self.root/"cli/session.json").read_text())["feature_events"], 4)

    @unittest.skipUnless(os.name == "posix", "virtual serial test requires POSIX")
    def test_serial_adapter_with_virtual_terminal(self):
        import pty
        master, slave = pty.openpty()
        try:
            with serial_lines(os.ttyname(slave), 0.1) as lines:
                os.write(master, (json.dumps(event())+"\n").encode())
                summary = record(lines, self.root/"virtual_serial", "fake_session", "fake_device",
                                 "synthetic", "serial")
            self.assertTrue(summary["complete"])
            self.assertEqual(summary["feature_events"], 1)
        finally:
            os.close(master)
            os.close(slave)


if __name__ == "__main__":
    unittest.main()
