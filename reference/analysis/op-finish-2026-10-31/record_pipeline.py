"""Bind the final queued publisher to actual normal and native test outputs."""
import hashlib
import json
import shutil
import struct
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op-pipeline"
sys.path.insert(0,str(ROOT/"tools"))
from verify_score_display_delivery import item,engine_hash,decimal_sections
from audit_vic_native_kernels import sections

def normalized_hunk(folder):
    data=bytearray((folder/"bruce_amiga.exe").read_bytes())
    layout=dict(sections(folder/"bruce_amiga.elf")[1])
    sizes=iter(layout[n][5] for n in (".text",".rodata",".data"))
    pos=0
    def word():
        nonlocal pos
        value=struct.unpack_from(">I",data,pos)[0];pos+=4;return value
    assert word()==1011 and word()==0
    count=word();word();word();pos+=4*count
    while pos<len(data):
        kind=word()
        if kind in (1001,1002):
            length=word()*4;size=next(sizes);assert 0<=length-size<=4
            data[pos+size:pos+length]=bytes(length-size);pos+=length
        elif kind==1003:word()
        elif kind==1004:
            while (count:=word()):pos+=4*(count+1)
        elif kind==1008:
            while (count:=word()):
                end=pos+count*4;zero=data.find(0,pos,end)
                if zero>=0:data[zero:end]=bytes(end-zero)
                pos=end+4
        elif kind in (1000,1009):
            length=word();pos+=length*4
        else:assert kind==1010
    return data

def main():
    original=json.loads((HERE/"result.json").read_text())
    tested=WORK/"tested";normal=ROOT/"amiga/out"
    assert (tested/"bruce_amiga.elf").read_bytes()==(normal/"bruce_amiga.elf").read_bytes()
    assert normalized_hunk(tested)==normalized_hunk(normal)
    # elf2hunk leaves nondeterministic allocation/name padding. Retain
    # precisely the EXE/ADF exercised by the owned normal UI runs.
    for name in ("bruce_amiga.exe","bruce_amiga.adf"):shutil.copyfile(tested/name,normal/name)
    shutil.copyfile(tested/"bruce_amiga.exe",ROOT/".tmp/amiga-boot/c/start")
    out=HERE/"pipeline-runs";out.mkdir(exist_ok=True)
    names={"final-still":"still-a","final-still-b":"still-b","final-move":"move-a","final-move2":"move-b",
           "final-stairs":"stairs","final-yamo":"yamo","long-release-a":"long-a","long-release-b":"long-b",
           "pipeline-tour-a":"tour-a","pipeline-tour-b":"tour-b"}
    for name,folder in names.items():
        src=WORK/folder
        dest=out/(folder+".txt");shutil.copyfile(src/"op0-light.txt",dest)
        original["runs"][name]=dict(report=item(dest),exe_sha256=item(src/"bruce_amiga.exe")["sha256"],route=(src/"op0-route.bin").read_bytes().hex())
    for mode in ("cli","adf"):
        shutil.copyfile(ROOT/f".tmp/op-finish/pipeline-{mode}/normal.json",out/f"normal-{mode}.json")
    for scene in ("stairs","death"):
        shutil.copyfile(ROOT/f"reference/analysis/render-coherence-2026-10-29/pipeline-render-{scene}/report.json",out/f"render-{scene}.json")
    native=(WORK/"native-copy/proof.bin").read_bytes()
    assert struct.unpack(">III",native)==(96,0,1)
    (out/"copy-proof.bin").write_bytes(native)
    actual=(ROOT/"core/c64_rooms.c").read_text()
    assert (WORK/"candidate/c64_rooms.c").read_text()==actual
    assert (WORK/"candidate/c64_actor_programs.h").read_bytes()==(ROOT/"core/c64_actor_programs.h").read_bytes()
    assert engine_hash(WORK/"candidate/c64_rooms.o")==engine_hash(ROOT/"amiga/out/c64_rooms.o")
    original["engine_sections"]=decimal_sections(ROOT/"amiga/out/c64_rooms.o")
    original["normal_build"]=[item(ROOT/e["path"]) for e in original["normal_build"]]
    original["inputs"]=[item(ROOT/e["path"]) for e in original["inputs"]]
    original["pipeline"]=True
    original["evidence"] += [item(p) for p in out.glob("*.json")]
    original["evidence"].append(item(out/"copy-proof.bin"))
    original["copy_kernel_sha256"]=hashlib.sha256((ROOT/"amiga/sprite_copy.s").read_bytes()).hexdigest()
    (HERE/"pipeline-result.json").write_text(json.dumps(original,indent=2)+"\n")

if __name__=="__main__":main()
