"""Evaluate immersion predictions on an exactly verified EEG-SVRec sample."""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import sklearn
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from audit import REVISION, audit

ALPHAS = [0.1, 1, 10, 100]


def evaluate(cache):
    rows, alignment = audit(cache)
    if alignment["verified_participants"] != [1] or len(rows) < 30:
        raise ValueError("Review the protocol before using a different paired benchmark sample.")
    y = np.array([r["metadata"]["immersion"] for r in rows], dtype=float)
    eeg = np.array([r["eeg"] for r in rows]).reshape(-1, 62, 5)
    behavior = []
    for row in rows:
        record = row["metadata"]
        duration = record["video_duration"]
        watch = (record["end_time"] - record["start_time"]) / 1000
        behavior.append([min(watch / duration, 1), np.log1p(duration), record["like"]])
    behavior = np.asarray(behavior)
    inputs = {
        "behavior": behavior,
        "eeg_summary": np.column_stack([behavior, eeg.mean(axis=1), eeg.std(axis=1)]),
        "eeg_channels": np.column_stack([behavior, eeg.reshape(len(rows), -1)]),
    }
    if not all(np.isfinite(x).all() for x in inputs.values()):
        raise ValueError("Verified sample contains non-finite features.")
    train_end = int(len(rows) * .7)
    fit_end = int(train_end * .75)
    predictions = {"train_mean": np.full(len(rows) - train_end, y[:train_end].mean())}
    selection = {}
    for name, x in inputs.items():
        validation = {}
        for alpha in ALPHAS:
            model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
            model.fit(x[:fit_end], y[:fit_end])
            pred = np.clip(model.predict(x[fit_end:train_end]), 1, 5)
            validation[str(alpha)] = float(np.abs(pred - y[fit_end:train_end]).mean())
        alpha = min(ALPHAS, key=lambda a: validation[str(a)])
        model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
        model.fit(x[:train_end], y[:train_end])
        predictions[name] = np.clip(model.predict(x[train_end:]), 1, 5)
        selection[name] = {"alpha": alpha, "validation_mae": validation}
    replay = []
    for index, row in enumerate(rows[train_end:]):
        replay.append({
            "participant": row["participant"], "item": row["item"],
            "video_order": row["video_order"], "session": row["session"],
            "observed": float(y[train_end + index]),
            "predictions": {name: float(value[index]) for name, value in predictions.items()},
        })
    summary = {
        "protocol": "Verified participant 01 sample; chronological 70/30 split; inner chronological validation",
        "verified_pairs": len(rows), "train_rows": train_end, "test_rows": len(replay),
        "inner_fit_rows": fit_end, "inner_validation_rows": train_end - fit_end,
        "mae": {name: float(np.abs(value - y[train_end:]).mean()) for name, value in predictions.items()},
        "model_selection": selection,
        "limitations": [
            "Single participant and a small test segment.",
            "Upstream EEG features use full-recording normalization.",
            "Post-view prediction with observed viewing behavior; unsuitable for prospective ranking claims.",
            "Clip-level predictions do not resolve within-video emotional change.",
        ],
    }
    splits = [{
        "participant": row["participant"], "item": row["item"], "eeg_index": row["eeg_index"],
        "video_order": row["video_order"],
        "split": "test" if i >= train_end else "inner_validation" if i >= fit_end else "inner_fit",
    } for i, row in enumerate(rows)]
    manifest = {
        "revision": REVISION, "python": platform.python_version(),
        "numpy": np.__version__, "sklearn": sklearn.__version__, "alpha_grid": ALPHAS,
        "code_sha256": {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                        for name in ["audit.py", "evaluate.py"]},
    }
    return {
        "audit.json": alignment, "summary.json": summary, "splits.json": splits,
        "replay.json": {"schema": "neuro-flow-replay-v1", "scope": summary["protocol"], "rows": replay},
        "manifest.json": manifest,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="New output directory for this run.")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output directory to preserve previous runs.")
    artifacts = evaluate(args.cache / REVISION)
    args.output.mkdir(parents=True)
    for name, content in artifacts.items():
        (args.output / name).write_text(json.dumps(content, indent=2, allow_nan=False) + "\n")
    print(json.dumps(artifacts["summary.json"], indent=2))
