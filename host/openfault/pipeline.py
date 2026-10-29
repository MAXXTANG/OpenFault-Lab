"""Session-separated offline evaluation of the original C features (MIT)."""
import hashlib
import json
import math
from pathlib import Path
import random
import re
import struct
import subprocess
import tempfile
import wave

RATE, WINDOW = 16000, 1024
FLOOR, THRESHOLD, CONSECUTIVE = 0.005, 6.0, 3
SLUG = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")


def dump(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def intervals(value, count):
    if not isinstance(value, list):
        raise ValueError("anomalous_intervals must be a list")
    previous = 0
    for item in value:
        if (not isinstance(item, list) or len(item) != 2 or
                any(type(x) is not int for x in item)):
            raise ValueError("Each interval must contain two integer window indices")
        start, end = item
        if not 0 <= start < end <= count or start < previous:
            raise ValueError("Intervals must be ordered, nonoverlapping, and within the session")
        previous = end
    return value


def load_manifest(path):
    path = Path(path).resolve()
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError("Manifest must be an object")
    if type(doc.get("version")) is not int or doc["version"] != 1:
        raise ValueError("Unsupported manifest version")
    if doc.get("provenance") not in ("synthetic", "measured"):
        raise ValueError("Declare provenance: synthetic or measured")
    if doc.get("split_unit") not in ("session", "device"):
        raise ValueError("Declare split_unit: session or device")
    if not isinstance(doc.get("dataset_license", "UNRELEASED"), str):
        raise ValueError("dataset_license must be a string")
    sessions = doc.get("sessions")
    if not isinstance(sessions, list) or not sessions:
        raise ValueError("Manifest needs sessions")
    seen, resolved_paths = set(), set()
    for session in sessions:
        if not isinstance(session, dict):
            raise ValueError("Each session must be an object")
        for key in ("session_id", "device_id"):
            if not isinstance(session.get(key), str) or not SLUG.fullmatch(session[key]):
                raise ValueError(f"Invalid {key}")
        if session["session_id"] in seen:
            raise ValueError("A session cannot appear in more than one split")
        seen.add(session["session_id"])
        if not isinstance(session.get("condition", "unspecified"), str):
            raise ValueError("condition must be a string")
        if session.get("split") not in ("train", "test"):
            raise ValueError("split must be train or test")
        if not isinstance(session.get("wav"), str):
            raise ValueError("Each session needs a relative WAV path")
        relative = Path(session["wav"])
        source = (path.parent / relative).resolve()
        if relative.is_absolute() or not source.is_relative_to(path.parent):
            raise ValueError("WAV paths must remain inside the manifest directory")
        if source in resolved_paths:
            raise ValueError("The same recording cannot appear twice")
        resolved_paths.add(source)
        if session.get("tail_policy", "error") not in ("error", "drop"):
            raise ValueError("tail_policy must be error or drop")
        if session["split"] == "train" and session.get("anomalous_intervals") != []:
            raise ValueError("Training sessions must be labeled normal")
    train = [s for s in sessions if s["split"] == "train"]
    test = [s for s in sessions if s["split"] == "test"]
    if not train or not test:
        raise ValueError("Both train and test sessions are required")
    train_devices = {s["device_id"] for s in train}
    test_devices = {s["device_id"] for s in test}
    if doc["split_unit"] == "device":
        if train_devices & test_devices:
            raise ValueError("Device split leaks a device across train/test")
    elif not test_devices <= train_devices:
        raise ValueError("Session split needs normal training data for every test device")
    return doc, path.parent


def extract(executable, source, output, tail_policy):
    digest = hashlib.sha256()
    with wave.open(str(source), "rb") as recording:
        if (recording.getnchannels(), recording.getsampwidth(), recording.getframerate(),
                recording.getcomptype()) != (1, 2, RATE, "NONE"):
            raise ValueError("WAV must be uncompressed PCM16 mono at 16000 Hz")
        frames = recording.getnframes()
        if frames < WINDOW or frames > RATE * 3600:
            raise ValueError("Recordings must contain a complete window and be at most one hour")
        dropped = frames % WINDOW
        if dropped and tail_policy != "drop":
            raise ValueError("Partial final window: explicitly choose tail_policy=drop")
        used = frames - dropped
        with tempfile.TemporaryDirectory(prefix="openfault-pcm-") as temp:
            pcm = Path(temp)/"input.pcm"
            remaining = used
            with pcm.open("wb") as raw:
                while remaining:
                    n = min(remaining, RATE)
                    data = recording.readframes(n)
                    if len(data) != n * 2:
                        raise ValueError("Truncated WAV payload")
                    digest.update(data)
                    raw.write(data)
                    remaining -= n
            with output.open("x", encoding="utf-8") as stream:
                result = subprocess.run([str(executable), str(pcm)], stdout=stream,
                                        stderr=subprocess.PIPE, text=True, check=False)
            if result.returncode:
                raise ValueError("C feature extractor failed: " + result.stderr.strip())
    # One recording's feature set at a time; the raw PCM is never kept in the result folder.
    features = [json.loads(line) for line in output.read_text().splitlines()]
    if len(features) != used // WINDOW:
        raise ValueError("Feature count does not match input duration")
    return features, digest.hexdigest(), dropped


def fit(values):
    n, mean, m2 = 0, 0.0, 0.0
    for value in values:
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("Invalid RMS feature")
        n += 1
        delta = value - mean
        mean += delta/n
        m2 += delta*(value-mean)
    if n < 32:
        raise ValueError("At least 32 normal training windows are required per baseline")
    return {"windows": n, "mean": mean, "stddev": math.sqrt(max(0.0, m2/(n-1)))}


def predict(values, model):
    predictions, scores, consecutive = [], [], 0
    for value in values:
        score = abs(value-model["mean"])/max(FLOOR, model["stddev"])
        consecutive = min(CONSECUTIVE, consecutive+1) if score >= THRESHOLD else 0
        scores.append(score)
        predictions.append(int(consecutive >= CONSECUTIVE))
    return predictions, scores


def metrics(rows):
    tp = fp = tn = fn = false_alerts = normal_windows = 0
    latencies, detected, total_intervals = [], 0, 0
    for row in rows:
        labels, predictions = row["labels"], row["predictions"]
        last_false = False
        for truth, prediction in zip(labels, predictions, strict=True):
            tp += truth == 1 and prediction == 1
            fp += truth == 0 and prediction == 1
            tn += truth == 0 and prediction == 0
            fn += truth == 1 and prediction == 0
            normal_windows += truth == 0
            is_false = truth == 0 and prediction == 1
            false_alerts += is_false and not last_false
            last_false = is_false
        for start, end in row["anomalous_intervals"]:
            total_intervals += 1
            first = next((i for i in range(start, end) if predictions[i]), None)
            if first is not None:
                detected += 1
                latencies.append((first+1-start)*WINDOW/RATE*1000)
    divide = lambda a, b: a/b if b else None
    return {"confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
            "precision": divide(tp, tp+fp), "recall": divide(tp, tp+fn),
            "f1": divide(2*tp, 2*tp+fp+fn),
            "normal_exposure_seconds": normal_windows*WINDOW/RATE,
            "false_alert_episodes": false_alerts,
            "false_alerts_per_hour": divide(false_alerts*3600, normal_windows*WINDOW/RATE),
            "detected_intervals": detected, "total_intervals": total_intervals,
            "window_detection_delays_ms": latencies,
            "mean_window_detection_delay_ms": divide(sum(latencies), len(latencies)),
            "delay_basis": "end of first detected PCM window minus annotated onset; excludes compute and IO"}


def evaluate(manifest, executable, output):
    doc, base = load_manifest(manifest)
    executable = Path(executable).resolve()
    output = Path(output).resolve()
    if not executable.is_file():
        raise ValueError("Build pcm_features first")
    output.mkdir(parents=True, exist_ok=False)
    feature_dir = output/"features"
    feature_dir.mkdir()
    sessions, hashes = [], {}
    for source in doc["sessions"]:
        session = dict(source)
        try:
            data, pcm_hash, dropped = extract(executable, base/source["wav"],
                feature_dir/(source["session_id"]+".jsonl"), source.get("tail_policy", "error"))
        except (wave.Error, EOFError) as error:
            raise ValueError("Invalid or truncated WAV header/encoding") from error
        if pcm_hash in hashes:
            raise ValueError("Identical PCM content reused across sessions: " + hashes[pcm_hash])
        hashes[pcm_hash] = source["session_id"]
        session["anomalous_intervals"] = intervals(source.get("anomalous_intervals"), len(data))
        session.update(features=data, pcm_sha256=pcm_hash, dropped_tail_samples=dropped)
        sessions.append(session)
    models = {}
    train = [s for s in sessions if s["split"] == "train"]
    if doc["split_unit"] == "device":
        models["pooled"] = fit(f["ac_rms"] for s in train for f in s["features"])
    else:
        for device in sorted({s["device_id"] for s in train}):
            models[device] = fit(f["ac_rms"] for s in train if s["device_id"] == device for f in s["features"])
    rows = []
    for session in sessions:
        if session["split"] != "test":
            continue
        values = [f["ac_rms"] for f in session["features"]]
        model = models["pooled" if doc["split_unit"] == "device" else session["device_id"]]
        predictions, scores = predict(values, model)
        labels = [0]*len(values)
        for start, end in session["anomalous_intervals"]:
            labels[start:end] = [1]*(end-start)
        rows.append({"session_id": session["session_id"], "device_id": session["device_id"],
                     "condition": str(session.get("condition", "unspecified")),
                     "anomalous_intervals": session["anomalous_intervals"],
                     "labels": labels, "predictions": predictions, "scores": scores,
                     "ac_rms": values, "dominant_hz": [f["dominant_hz"] for f in session["features"]]})
    result = {"version": 1, "provenance": doc["provenance"], "split_unit": doc["split_unit"],
              "sample_rate": RATE, "window_samples": WINDOW,
              "dataset_license": doc.get("dataset_license", "UNRELEASED"),
              "features_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "baseline": {"feature": "ac_rms", "scope": "pooled" if doc["split_unit"] == "device" else "per_device",
                           "stddev_floor": FLOOR, "threshold": THRESHOLD, "consecutive": CONSECUTIVE,
                           "models": models},
              "sessions": [{k: v for k, v in s.items() if k != "features"} for s in sessions],
              "metrics": metrics(rows), "test_sessions": rows,
              "limitations": ["RMS-only scoring can miss frequency-only changes.",
                  "Thresholds are fixed before test evaluation; no test-data fitting.",
                  "Offline baseline uses all normal training windows and Python double arithmetic; firmware calibrates 32 windows with float arithmetic.",
                  "Window detection delay is not measured inference latency.",
                  "No raw PCM is retained in this result; source WAVs remain at their original location.",
                  "Exact duplicate recordings are rejected; edited or overlapping excerpts require a separate provenance audit.",
                  "False-alert rate is normalized to observed normal exposure; short recordings cannot establish long-term reliability."]}
    dump(output/"result.json", result)
    from .report import render_report
    (output/"report.html").write_text(render_report(result), encoding="utf-8")
    return result


def make_demo(output):
    """Write deterministic synthetic WAV sessions; never label them measured."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    rng = random.Random(20261029)
    specs = [("train_a", "train", "steady", []), ("train_b", "train", "steady", []),
             ("test_normal", "test", "steady", []),
             ("test_amplitude", "test", "amplitude_step", [[32, 64]]),
             ("test_frequency", "test", "frequency_only", [[32, 64]])]
    sessions = []
    for name, split, condition, changes in specs:
        with wave.open(str(output/(name+".wav")), "wb") as stream:
            stream.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
            for window in range(96):
                changed = 32 <= window < 64
                amplitude = 0.5 if condition == "amplitude_step" and changed else 0.25
                hz = 2000 if condition == "frequency_only" and changed else 1000
                samples = [int(32767*(amplitude*math.sin(2*math.pi*hz*(window*WINDOW+i)/RATE)+rng.uniform(-0.002, 0.002))) for i in range(WINDOW)]
                stream.writeframes(struct.pack("<"+"h"*WINDOW, *samples))
        sessions.append({"session_id": name, "device_id": "synthetic_fan", "split": split,
                         "wav": name+".wav", "condition": condition, "anomalous_intervals": changes})
    dump(output/"manifest.json", {"version": 1, "provenance": "synthetic", "split_unit": "session",
         "dataset_license": "UNRELEASED", "sessions": sessions})
    return output/"manifest.json"
