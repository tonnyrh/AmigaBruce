"""Validate whole-route timings and the exact builds used for the VIC pair change."""
import hashlib
import json
from pathlib import Path
from audit_vic_native_kernels import sections
from capture_paula_stream import elf_symbols

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "reference/analysis/op2-vic-pairs-2026-10-31"
CHAIN = ROOT / "reference/analysis/actor-chain-2026-10-26"
VALIDATION = ROOT / "reference/validation"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def item(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def linked_pair_hash(elf, kernel):
    data, headers = sections(elf)
    symbols = elf_symbols(elf)[1]
    text = dict(headers)[".text"]
    offset = symbols["source_vic_flat_pair"] - text[3]
    assert 0 <= offset <= text[5] - kernel["size"]
    start = text[4] + offset
    code = bytearray(data[start:start + kernel["size"]])
    for address, symbol in kernel["absolute_operands"]:
        assert int.from_bytes(code[address:address+4], "big") == symbols[symbol]
        code[address:address+4] = bytes(4)
    return hashlib.sha256(code).hexdigest()


def verify_current():
    evidence = read(STAGE / "measurements.json")
    previous = read(STAGE / "previous-delivery.json")
    frozen = ROOT / ".reference/c64/work/untrained-memory.bin"
    assert item(frozen)["sha256"] == previous["source_sha256"] == evidence["c64_sha256"]
    assert item(STAGE / "previous-delivery.json")["sha256"] == evidence["previous_delivery_sha256"]
    source = frozen.read_bytes()
    assert source[0x29ce:0x29d4] == bytes.fromhex("ad 1e d0 d0 01 60")
    assert source[0x3d20:0x3d28] == bytes.fromhex("ad 1e d0 aa 29 03 f0 10")
    for entry in evidence["inputs"] + evidence["normal_build"]:
        assert item(ROOT / entry["path"]) == entry, entry["path"]
    assert evidence["normal_build"][0]["sha256"] == evidence["normal_build"][-1]["sha256"]
    assert evidence["candidate_engine_sections"] == evidence["normal_engine_sections"]

    comparisons = []
    for room, enemy, route, before, after in (
        (1, 3, 0, "baseline1", "trial1"), (1, 3, 0, "baseline2", "trial2"),
        (12, 3, 1, "stairs-control-before", "stairs-control-after"),
        (13, 1, 0, "yamo-before", "yamo-after")
    ):
        pair = []
        for name, variant in ((before, "before"), (after, "candidate")):
            path = STAGE / (name + ".txt")
            assert item(path)["sha256"] == evidence["runs"][name]["report_sha256"]
            assert evidence["runs"][name]["route_hex"] == bytes((room-1,enemy,route,0,0,240,0,240)).hex()
            assert evidence["runs"][name]["exe_sha256"] == evidence["probe_exe_sha256"][variant]
            report = dict(line.split("=", 1) for line in path.read_text().splitlines() if "=" in line)
            for key, wanted in dict(room=room, enemy_mask=enemy, input_route=route, warmup_steps=240,
                    steps=240, finished=1, restored_os=1, source_profile=0, visited_rooms=1 << (room-1),
                    source_fault=0, audio_fault=0, dma_fault=0).items():
                assert int(report[key]) == wanted, (name, key)
            assert int(report["chip_largest_loaded"]) >= 49152
            active = list(map(int, report["active_loops"].split(",")))
            assert active[0 if room==12 else enemy] == sum(active) == int(report["loops"])
            assert room!=12 or int(report["climb_steps"])==240
            pair.append((int(report["pal_fields"]), int(report["audio_missed"])))
        (fields, misses), (new_fields, new_misses) = pair
        comparisons.append(dict(room=room, before_fields=fields, after_fields=new_fields,
                                before_missed=misses, after_missed=new_misses))
        if room == 1:
            assert new_fields < fields and new_misses < misses
        else:
            assert new_fields <= fields and new_misses <= misses
    vic = read(VALIDATION / "source-vic-host.json")
    actor = read(CHAIN / "report.json")
    world = read(CHAIN / "integrated-controls.json")
    native = read(VALIDATION / "source-world-native.json")
    assert vic["calls"]==8741 and vic["pair_basis_cases"]==48**3
    assert actor["checks"]==len(actor["rows"])==3034
    assert world["instructions"]==7055873 and len(world["checks"])==5
    for report in (vic, actor, world, native):
        for entry in report["source_files"]:
            assert item(ROOT / entry["path"]) == entry, entry["path"]
    for entry in native["build"]:
        assert item(ROOT / entry["path"]) == entry, entry["path"]
    kernel = evidence["kernel"]
    for elf in (ROOT/"amiga/out/bruce_amiga.elf",
                ROOT/next(entry["path"] for entry in native["build"] if entry["path"].endswith(".elf"))):
        assert linked_pair_hash(elf, kernel) == kernel["sha256"], elf
    run = native["run"]
    assert not native["failures"] and run["restored_os"]=="1"
    assert int(run["source_actor_fixture_cases"])==53 and int(run["frames"])==1200
    assert int(run["chip_largest_loaded"])>=49152
    proofs = [STAGE / "measurements.json", STAGE / "previous-delivery.json", STAGE / "candidate.patch",
              CHAIN / "report.json", CHAIN / "integrated-controls.json", VALIDATION / "source-vic-host.json",
              VALIDATION / "source-world-native.json", Path(__file__).resolve()]
    for mode in ("cli","adf"):
        path = STAGE/"boot"/mode/"report.json"
        boot = read(path)
        assert boot["mode"]==mode and boot["complete_menu"]
        assert boot["normal_exe_sha256"]==evidence["normal_build"][0]["sha256"]
        assert boot["elf"]==item(ROOT/"amiga/out/bruce_amiga.elf")
        for entry in boot["artifacts"]:
            assert item(ROOT/entry["path"])==entry, entry["path"]
        if mode=="adf":
            states=boot["game_states"]
            assert len(states)>=2 and states[-1]["steps"]>states[0]["steps"]
            assert all(state["fault"]==0 and state["room"]==1 for state in states)
        proofs.append(path)
    return dict(previous, status="scoped_vic_pair_overlap_realtime_open", op2_pairs=comparisons,
                normal_build=evidence["normal_build"], largest_chip_block=int(run["chip_largest_loaded"]),
                realtime_gate_passed=False, artifacts=[item(path) for path in proofs])


if __name__ == "__main__":
    verify_current()
    print("PASS VIC pair build, eight PAL runs and C64/native controls")
