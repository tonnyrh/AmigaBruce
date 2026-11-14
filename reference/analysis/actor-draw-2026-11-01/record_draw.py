"""Record the tested display change against the previous field-work delivery."""
import json
import hashlib
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORK = ROOT / ".tmp/actor-draw"
NORMAL = ROOT / "amiga/out"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(HERE.parent / "op-finish-2026-10-31"))
from record_pipeline import normalized_hunk, sections
from verify_score_display_delivery import decimal_sections, item


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def archive(source, name):
    target = HERE / "runs" / name
    shutil.copyfile(source, target)
    return item(target)


def allocated(elf):
    raw, headers = sections(elf)
    return [(name, h[3], h[5], raw[h[4]:h[4]+h[5]] if h[1] != 8 else b"")
            for name, h in headers if h[2] & 2]


def main():
    (HERE / "runs").mkdir(exist_ok=True)
    parent_path = HERE.parent / "field-work-2026-11-01/delivery.json"
    parent = read(parent_path)
    base = ROOT / ".tmp/field-work/release"
    trial = WORK / "retail-actors"
    assert normalized_hunk(trial) == normalized_hunk(NORMAL)
    assert allocated(trial / "bruce_amiga.elf") == allocated(NORMAL / "bruce_amiga.elf")
    assert decimal_sections(NORMAL / "c64_rooms.o") == decimal_sections(trial / "c64_rooms.o") == decimal_sections(WORK / "actors/c64_rooms.o")
    assert decimal_sections(NORMAL / "source_dma.o") == decimal_sections(base / "source_dma.o") == parent["dma_sections"]
    hooks = (ROOT / "core/c64_actor_programs.h").read_text()
    poll = "if(source_audio_poll)source_audio_poll();\n"
    assert hooks.count(poll) == 3 and hooks.replace(poll,"") == (base / "c64_actor_programs.h").read_text()

    runs = {}
    for label, folder in (("direct-a","actors-short-a"), ("direct-b","actors-short-b"),
                          ("direct-still-a","actors-still-a"), ("direct-still-b","actors-still-b"),
                          ("long-direct-a","actors-long-a"), ("long-direct-b","actors-long-b"),
                          ("direct-stairs","actors-stairs"), ("direct-yamo","actors-yamo")):
        folder = WORK / folder
        rows = dict(l.split("=",1) for l in (folder / "op0-light.txt").read_text().splitlines() if "=" in l)
        assert rows["finished"] == rows["restored_os"] == "1"
        assert rows["paula_publications"] == rows["pal_fields"]
        assert all(rows[key]=="0" for key in ("audio_missed","paula_empty","paula_double","source_fault","audio_fault","dma_fault"))
        runs[label] = dict(raw=archive(folder / "op0-light.txt", label+".txt"),
                           exe=item(folder / "bruce_amiga.exe")["sha256"],
                           route=(folder / "op0-route.bin").read_bytes().hex())
    ui = {}
    for mode in ("cli", "adf"):
        path = ROOT / f".tmp/op-finish/draw-actors-check-{mode}/normal.json"
        r = read(path)
        assert r["normal_exe_sha256"] == item(trial / "bruce_amiga.exe")["sha256"]
        assert r["complete_menu"] and r["pause_preserved"] and r["fields"] >= 6000 and r["misses"] == 0
        if mode == "cli": assert r["joystick_crossings"] == [2,1]
        else: assert r["turn_after_death"]["player"] == 2
        ui[mode] = archive(path, "normal-"+mode+".json")
    replacements = {}
    for scene in ("stairs", "death"):
        path = ROOT / f"reference/analysis/render-coherence-2026-10-29/draw-actors-render-{scene}/report.json"
        replacements[scene] = archive(path, "render-"+scene+".json")
    replacements["alloc-release/allocation.json"] = archive(ROOT / ".tmp/field-work/actors-alloc/allocation.json", "allocation.json")
    old_world = WORK / "previous/source-world-native.json"
    assert item(old_world)["sha256"] == next(ref["sha256"] for ref in parent["proofs"]
                                              if ref["path"] == "reference/validation/source-world-native.json")
    prior_replay = archive(old_world,"previous-replay.json")
    world = read(ROOT / "reference/validation/source-world-native.json")
    assert not world["failures"]
    old_pixels = (WORK / "previous/autotest-frame.bpl").read_bytes()
    pixels = (NORMAL / "autotest-frame.bpl").read_bytes()
    assert len(pixels) == 40960 and pixels == old_pixels
    pixel_hash = 2166136261
    for value in pixels:
        pixel_hash = ((pixel_hash ^ value) * 16777619) & 0xffffffff
    assert str(pixel_hash) == world["run"]["capture_original_hash"] == read(old_world)["run"]["capture_original_hash"]
    for name in ("bruce_amiga.exe", "bruce_amiga.adf"):
        shutil.copyfile(trial / name, NORMAL / name)
    shutil.copyfile(trial / "bruce_amiga.exe", ROOT / ".tmp/amiga-boot/c/start")
    result = dict(predecessor=item(parent_path), production_mode="direct",
                  engine_sections=decimal_sections(NORMAL / "c64_rooms.o"),
                  image_bytes=len(pixels), image_sha256=hashlib.sha256(pixels).hexdigest(),
                  normal_build=[item(ROOT / r["path"]) for r in parent["normal_build"]],
                  diagnostic_exe=item(WORK / "actors/bruce_amiga.exe")["sha256"], runs=runs, ui=ui,
                  proofs=[item(ROOT / r["path"]) for r in parent["proofs"]],
                  field_evidence=replacements, prior_replay=prior_replay,
                  profile=archive(WORK / "profile-first/op0-light.txt","profile.txt"),
                  interpolation_only=archive(WORK / "pose-a/op0-light.txt","interpolation-only.txt"),
                  audio_seams=archive(WORK / "seams.json","audio-seams.json"),
                  traced_miss=archive(WORK / "trace-long-a/op0-light.txt","traced-miss.txt"),
                  without_audio_checks=[archive(WORK / f"long-{s}/op0-light.txt",f"before-audio-{s}.txt") for s in ("a","b")])
    manifest = HERE / "delivery.json"
    manifest.write_text(json.dumps(result, indent=2)+"\n")
    source = read(WORK / "seams.json")
    evidence = dict(capture_id="ACTOR-DRAW-0001",reference_id="c64-local-t64-remember-no-trainers",
                    source_sha256=source["source_sha256"],code_sites=source["sites"],
                    status="candidate_code_and_scoped_pal_measurements",edition_verified=False,
                    full_original_parity=False,artifacts=[item(manifest),result["audio_seams"],result["traced_miss"]])
    (ROOT / "docs/parity/evidence/ACTOR-DRAW-0001.json").write_text(json.dumps(evidence,indent=2)+"\n")


if __name__ == "__main__":
    main()
