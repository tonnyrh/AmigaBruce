"""Verify OP1 row equivalence, the actual linked kernel and the OP0 timing pairs."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from audit_vic_native_kernels import sections
from capture_paula_stream import elf_symbols

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/"reference/analysis/op1-row-walk-2026-10-31"
OP0 = BASE.parent/"op0-light-2026-10-31"
BINARY = ROOT/".reference/c64/work/untrained-memory.bin"
REPORT = BASE/"result.json"
PAIRS = [("op1-parent-1","both-1"),("op1-parent-2","both-2"),
         ("op1-parent-stairs","stairs-1"),("op1-parent-yamo13","yamo-13")]

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(folder):
    report = read(folder/"identity.json")
    for item in report["source_files"]:
        assert digest(ROOT/item["path"]) == item["sha256"], item["path"]
    row = dict(line.split("=",1) for line in (folder/"op0-light.txt").read_text().splitlines() if "=" in line)
    assert row == report["run"]
    assert row["steps"] == row["warmup_steps"] == "240"
    assert row["finished"] == row["restored_os"] == "1"
    assert all(row[key]=="0" for key in ("source_profile","source_fault","audio_fault","dma_fault"))
    return row

def code_in_elf(elf, kernel):
    raw, headers = sections(elf)
    _, symbols = elf_symbols(elf)
    pc = symbols["bl_contact_rows8"]
    text = dict(headers)[".text"]
    at = text[4] + pc - text[3]
    assert text[3] <= pc and pc+len(kernel) <= text[3]+text[5]
    assert raw[at:at+len(kernel)]==kernel, elf

def verify():
    source = read(BASE/"source-controls.json")
    assert digest(BINARY)==source["source_sha256"]
    assert digest(BASE/"proof/vectors.bin")==source["fixture_sha256"]
    assert struct.unpack(">HH",(BASE/"proof/proof-result.bin").read_bytes())==(192,0)
    assert source["cases"]==192 and source["executed_instructions"]==29747
    for name in ("proof","light"):
        for path, value in read(BASE/name/"inputs.json").items():
            assert digest(ROOT/path)==value,path
    data, headers = sections(BASE/"light/contact_rows.o")
    section = dict(headers)[".text.bl_contact_rows8"]
    kernel = data[section[4]:section[4]+section[5]]
    micro = []
    for i,(pre,one,two,post) in enumerate(struct.iter_unpack(">4I",(BASE/"micro/micro.bin").read_bytes())):
        assert max(one,two)<min(pre,post)
        micro.append(dict(rows=(1,4,8)[i%3], mask=("empty","sparse","dense")[i//3],
                          parent=[pre,post],candidate=[one,two], percent_less=round(100*(1-(one+two)/(pre+post)),2)))
    assert len(micro)==9
    fixture = read(BASE/"fixture/result.json")
    assert not fixture["failures"] and fixture["run"]["source_actor_fixture_cases"]=="53"
    assert fixture["run"]["frames"]=="1200" and fixture["run"]["source_actor_fixture_failure"]=="0"
    for item in fixture["source_files"]+fixture["build"]:
        assert digest(ROOT/item["path"])==item["sha256"],item["path"]
    for path in [BASE/"proof/bruce_amiga.elf", BASE/"micro/bruce_amiga.elf", BASE/"fixture/out/bruce_test.elf"]:
        code_in_elf(path,kernel)
    pairs=[]
    for parent, candidate in PAIRS:
        old=OP0/"runs"/parent
        new=BASE/"runs"/candidate
        before,after=run(old),run(new)
        assert (old/"op0-route.bin").read_bytes()==(new/"op0-route.bin").read_bytes()
        assert digest(old/"bruce_amiga.exe")==digest(OP0/"light/out/bruce_amiga.exe")
        assert digest(new/"bruce_amiga.exe")==digest(BASE/"light/bruce_amiga.exe")
        assert before["visited_rooms"]==after["visited_rooms"]
        for r in [before,after]:
            active=[int(n) for n in r["active_loops"].split(",")]
            expected=0 if r["room"]=="12" else int(r["enemy_mask"])
            assert active[expected]==sum(active)==int(r["loops"])
        code_in_elf(new/"bruce_amiga.elf",kernel)
        pairs.append(dict(parent=parent,candidate=candidate,
                          fields=[int(r["pal_fields"]) for r in [before,after]],
                          audio_missed=[int(r["audio_missed"]) for r in [before,after]],
                          work_lines=[int(r["work_lines"]) for r in [before,after]],
                          wait_lines=[int(r["wait_lines"]) for r in [before,after]]))
    assert pairs[0]["fields"][1]<pairs[0]["fields"][0] and pairs[1]["fields"][1]>=pairs[1]["fields"][0]
    paths=[BASE/name for name in ["rows.s","contact_rows.s","build.py","vectors.py","source-controls.json",
           "proof.c","micro.c","micro-build.py","proof/proof-result.bin","micro/micro.bin","fixture/result.json",
           "light/inputs.json","proof/inputs.json","run-private.ps1","test-fixture.ps1","fixture-build.ps1","run-fixture.ps1"]]
    for parent,candidate in PAIRS:
        paths.extend([OP0/"runs"/parent/"identity.json",BASE/"runs"/candidate/"identity.json"])
    paths += [ROOT/"tools/test-op1-row-walk.ps1",Path(__file__),ROOT/"amiga/contact_rows.s",ROOT/"amiga/out/bruce_amiga.exe"]
    assert digest(paths[-1])=="4229148ac5b324d8d5296594fd1364439a90550577796b913c1d9e6b559fa561"
    return dict(status="pilot_rejected_whole_game_gain_not_repeated",source=source,whole_ram_cases=192,
                pairs=pairs,isolated_rows=micro,fixture_cases=53,fixture_loops=1200,
                fixture_audio_missed=int(fixture["run"]["source_clock_missed"]),
                largest_chip=int(fixture["run"]["chip_largest_loaded"]),natural_playthrough=False,
                realtime_accepted=False,artifacts={p.relative_to(ROOT).as_posix():digest(p) for p in paths})

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--record",action="store_true")
    args=parser.parse_args()
    result=verify()
    if args.record:
        REPORT.write_text(json.dumps(result,indent=2)+"\n")
    else:
        assert read(REPORT)==result
    print(result["status"])
    for pair in result["pairs"]:
        print(pair["candidate"], pair["fields"], pair["audio_missed"])
