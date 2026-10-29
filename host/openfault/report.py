"""Self-contained diagnostic HTML; no external assets or executable content (MIT)."""
from html import escape
import math


def number(value):
    return "undefined" if value is None else f"{value:.3f}"


def chart(row, threshold):
    scores = row["scores"]
    width, height = 800, 170
    ceiling = max(12.0, min(120.0, max(scores, default=12.0)))
    x = lambda i: 35+(width-45)*i/max(1, len(scores))
    y = lambda value: height-20-(height-35)*min(ceiling, value)/ceiling
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Anomaly scores and annotated variation intervals">']
    for start, end in row["anomalous_intervals"]:
        parts.append(f'<rect x="{x(start):.2f}" y="10" width="{x(end)-x(start):.2f}" height="140" fill="#fde2e2"/>')
    parts.append(f'<line x1="35" x2="790" y1="{y(threshold):.2f}" y2="{y(threshold):.2f}" stroke="#b45309" stroke-dasharray="5 4"/>')
    stride = max(1, math.ceil(len(scores)/400))
    indices = sorted(set(range(0, len(scores), stride)) | {len(scores)-1})
    points = " ".join(f'{x(i):.2f},{y(scores[i]):.2f}' for i in indices)
    parts.append(f'<polyline points="{points}" stroke="#1d4ed8" stroke-width="2" fill="none"/>')
    parts.append(f'<text x="2" y="17">{ceiling:.0f}</text><text x="12" y="153">0</text><text x="35" y="168">window 0</text><text x="690" y="168">{len(scores)} windows</text></svg>')
    return "".join(parts)


def render_report(result):
    m = result["metrics"]
    synthetic = result["provenance"] == "synthetic"
    banner = ("SYNTHETIC SOFTWARE CHECK — NOT HARDWARE PERFORMANCE" if synthetic else
              "OFFLINE RECORDING EVALUATION — NOT ON-DEVICE PERFORMANCE")
    cards = "".join(f'<div class="card"><span>{escape(title)}</span><strong>{number(m[key])}</strong></div>' for title, key in [
        ("Window precision", "precision"), ("Window recall", "recall"), ("Window F1", "f1"),
        ("False alert episodes / normal hour", "false_alerts_per_hour")])
    confusion = "".join(f'<td>{m["confusion"][key]}</td>' for key in ["tn", "fp", "fn", "tp"])
    sessions = []
    for row in result["test_sessions"]:
        sessions.append(f'<section><h2>{escape(row["session_id"])}</h2><p>{escape(row["condition"])} · '
                        f'{sum(row["labels"])} annotated variation windows · {sum(row["predictions"])} predicted anomaly windows</p>'
                        + chart(row, result["baseline"]["threshold"]) +
                        '<p class="muted">Red shading: annotated variation. Blue: RMS score. Dashed: fixed threshold. '
                        'Plot subsamples long recordings and caps scores at 120; metrics use every window.</p></section>')
    notes = "".join(f'<li>{escape(note)}</li>' for note in result["limitations"])
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OpenFault Lab · offline evaluation</title><style>
body{{font:16px system-ui,sans-serif;background:#f1f5f9;color:#172033;margin:0}}main{{max-width:1000px;margin:auto;padding:28px}}h1{{font-size:34px}}h2{{font-size:22px}}.banner{{background:#78350f;color:white;padding:16px;border-radius:10px;font-weight:700}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:24px 0}}.card,section{{background:white;padding:20px;border-radius:12px;margin-bottom:14px}}.card span{{display:block;font-size:13px;color:#475569}}strong{{font-size:30px}}table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;padding:10px;border-bottom:1px solid #cbd5e1}}svg{{width:100%;font:11px system-ui}}.muted{{color:#475569;font-size:13px}}li{{margin:8px 0}}
</style><main><p>OPENFAULT LAB / HOST TOOLS</p><h1>Offline condition-monitoring evaluation</h1>
<div class="banner">{banner}</div><p>Baseline: AC RMS · split by {escape(result["split_unit"])} · train normal sessions only · no raw audio embedded</p>
<div class="cards">{cards}</div><section><h2>Confusion counts</h2><table><tr><th>True normal</th><th>False positive</th><th>Missed variation</th><th>Detected variation</th></tr><tr>{confusion}</tr></table>
<p>{m["detected_intervals"]}/{m["total_intervals"]} annotated intervals detected. Normal exposure: {m["normal_exposure_seconds"]:.3f} s.</p>
<p>Mean window detection delay: {number(m["mean_window_detection_delay_ms"])} ms. This excludes computation, serial I/O and device scheduling.</p></section>
{''.join(sessions)}<section><h2>Interpretation and limits</h2><ul>{notes}</ul><p>Dataset license status: {escape(str(result["dataset_license"]))}. Complete provenance, fitted parameters, hashes and window predictions are in result.json.</p></section></main></html>'''
