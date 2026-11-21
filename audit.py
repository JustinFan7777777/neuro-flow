"""Audit alignment against the authors' explicitly paired benchmark records."""
import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen

REVISION = "5f40c0476bde48d195de55c933293a0849977011"
BASE = f"https://raw.githubusercontent.com/hezy18/EEG-SVRec/{REVISION}"
BENCHMARK = "code/rec_benchmarch/EEGvRec_EEG_all.inter"
BENCHMARK_BLOB = "0b971089096864802b9388cfa2a390fb8478b177"


def load_bytes(cache, relative):
    path = cache / Path(relative).name
    if not path.exists():
        with urlopen(f"{BASE}/{relative}", timeout=30) as response:
            data = response.read()
        # Keep incomplete downloads out of the cache.
        temporary = path.with_suffix(".part")
        temporary.write_bytes(data)
        temporary.replace(path)
    return path.read_bytes()


def audit(cache):
    cache.mkdir(parents=True, exist_ok=True)
    hashes = {}
    metadata, features, inventory = {}, {}, []
    for participant in range(1, 31):
        for kind, relative in [
            ("metadata", f"data/metadata/{participant:02d}_behavior_MAES.json"),
            ("eeg", f"data/EEG_data/EEG_DE_avg/{participant:02d}_idx2de_nor_avg.json"),
        ]:
            data = load_bytes(cache, relative)
            hashes[relative] = hashlib.sha256(data).hexdigest()
            parsed = json.loads(data)
            (metadata if kind == "metadata" else features)[participant] = parsed
        orders = {str(record["video_order"] - 1) for record in metadata[participant].values()}
        inventory.append({
            "participant": participant,
            "metadata_rows": len(metadata[participant]),
            "eeg_rows": len(features[participant]),
            "feature_keys_without_matching_view_order": sorted(set(features[participant]) - orders, key=int),
            "alignment": "unverified outside paired benchmark",
        })

    payload = load_bytes(cache, BENCHMARK)
    blob_hash = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
    if blob_hash != BENCHMARK_BLOB:
        raise ValueError("Benchmark bytes do not match the pinned upstream Git blob.")
    hashes[BENCHMARK] = hashlib.sha256(payload).hexdigest()
    verified, rejected = [], []
    reader = csv.DictReader(io.StringIO(payload.decode()), delimiter="\t")
    seen = set()
    for line, record in enumerate(reader, start=2):
        sequence = record.get("EEG_data_310:float_seq")
        if not sequence or len(sequence.split()) != 310:
            rejected.append({"line": line, "reason": "incomplete benchmark row"})
            continue
        participant = int(record["user_id:token"]) + 1
        item = record["item_id:token"]
        eeg = list(map(float, sequence.split()))
        original = metadata[participant][item]
        for field, column in [
            ("video_order", "video_order:float"), ("start_time", "start_ts:float"),
            ("end_time", "end_ts:float"), ("immersion", "rating_immersion:float"),
        ]:
            if float(original[field]) != float(record[column]):
                raise ValueError(f"Metadata mismatch on benchmark line {line}, {field}.")
        matches = [
            key for key, matrix in features[participant].items()
            if [value for channel in matrix for value in channel] == eeg
        ]
        if len(matches) != 1:
            raise ValueError(f"EEG vector has {len(matches)} matches on line {line}.")
        key = (participant, item)
        if key in seen:
            raise ValueError("Duplicate benchmark interaction.")
        seen.add(key)
        verified.append({
            "participant": participant, "item": item,
            "video_order": original["video_order"], "session": original["session_id"],
            "eeg_index": matches[0], "metadata": original, "eeg": eeg,
        })
    verified.sort(key=lambda row: (row["participant"], row["video_order"]))
    return verified, {
        "revision": REVISION, "benchmark_git_blob": blob_hash, "source_sha256": hashes,
        "verified_pairs": len(verified), "verified_participants": sorted({r["participant"] for r in verified}),
        "inventory": inventory, "rejected_benchmark_rows": rejected,
        "finding": "The preprocessing assigns indices after filtering records. Viewing order alone does not establish alignment.",
        "scope": "Only exact benchmark-matched pairs are admitted to the new evaluation.",
    }
