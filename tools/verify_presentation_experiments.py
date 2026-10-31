"""Audit rejected presentation experiments without changing production timing."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "reference/analysis/present-2026-10-29"
RUNS = "reference/analysis/optimization-2026-10-27"

def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8-sig"))

def item(path):
    return dict(path=path, sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest())

def check(entry, path=None):
    assert item(path or entry["path"])["sha256"] == entry["sha256"], path or entry["path"]

def verify():
    paths = [BASE+"/baseline/manifest.json", BASE+"/probe-before/manifest.json", BASE+"/rejected-retry/manifest.json"]
    for folder in ("baseline", "probe-before", "rejected-retry"):
        for entry in read(BASE+"/"+folder+"/manifest.json")["files"]:
            check(entry, BASE+"/"+folder+"/"+entry["path"])
    source = ROOT/".reference/c64/work/untrained-memory.bin"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == "092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
    data = source.read_bytes()
    assert data[0x1bc2:0x1bc6] == bytes.fromhex("a9 03 85 48")
    assert data[0x1c32:0x1c39] == bytes.fromhex("a5 48 d0 fc 4c c2 1b")
    rows = []
    for label, variant in (("present-r01-before-scoped", "probe-before"), ("present-r01-retry-scoped", "rejected-retry")):
        folder = RUNS+"/"+label
        ident = read(folder+"/identity.json")
        for entry in ident["source_files"]:
            candidate = BASE+"/"+variant+"/"+entry["path"]
            if not (ROOT/candidate).exists():
                candidate = BASE+"/baseline/"+entry["path"]
            check(entry, candidate)
        for entry in ident["build"]:
            check(entry, folder+"/"+Path(entry["path"]).name)
        run = ident["run"]
        assert run["source_perf_steps"] == run["source_world_steps"] == "360"
        assert run["contact_kernel_cases"] == "710" and run["sprite_copy_cases"] == "256"
        assert run["vic_repeat_cases"] == "0" and run["restored_os"] == "1"
        for key in ("c64_room_fault", "source_audio_faults", "source_dma_faults", "runtime_arithmetic_errors", "vic_compare_errors", "contact_kernel_errors"):
            assert run[key] == "0", (label, key)
        assert int(run["chip_largest_loaded"]) >= 49152
        assert int(run["drawn_image_fields"])+int(run["held_image_fields"]) == int(run["frames"])
        assert int(run["max_held_image_streak"]) <= 3
        native = read(folder+"/native.json")
        assert not native["realtime_accepted"] and not native["natural_playthrough"]
        rows.append(dict(label=label, pal_fields=int(run["source_clock_elapsed"]), missed_audio_ticks=int(run["source_clock_missed"]), presentations=int(run["drawn_image_fields"]), deferrals=int(run["held_image_fields"]), blank_reuse_opportunities=int(run["present_probe_reuse"])))
        paths += [folder+"/"+f for f in ("identity.json", "native.txt", "native.json")]
    before, after = rows
    assert (before["pal_fields"], after["pal_fields"]) == (1429, 1415)
    assert (before["missed_audio_ticks"], after["missed_audio_ticks"]) == (25, 44)
    assert before["blank_reuse_opportunities"] == 2
    # The baseline archive records restoration at rejection time. Later
    # production changes are bound by the current delivery verifier.
    paths += ["tools/verify_presentation_experiments.py", "docs/PRESENTATION_EXPERIMENTS.md"]
    return dict(status="rejected_audio_regression_production_restored", source_sha256=hashlib.sha256(data).hexdigest(), edition_verified=False, natural_playthrough=False, realtime_accepted=False, source_steps=360, runs=rows, artifacts=[item(path) for path in paths])

def main():
    p=argparse.ArgumentParser();p.add_argument("--record", action="store_true");args=p.parse_args()
    result=verify();out=ROOT/"reference/validation/presentation-experiments.json"
    if args.record:
        out.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    else:
        assert read(out) == result
    print("PASS presentation experiment audit: 1429->1415 fields, audio misses 25->44; candidate rejected, production restored")

if __name__ == "__main__":
    main()
