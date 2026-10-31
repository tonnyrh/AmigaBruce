"""Verify the evidence for the A500 wide-monochrome VIC decoder delivery."""
import hashlib
import json
import struct
import sys
from pathlib import Path
from audit_vic_native_kernels import sections
from capture_paula_stream import elf_symbols

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/"reference/analysis/op2-field-2026-10-31"
PILOT=STAGE/"pilot"
PARENT=STAGE/"parent"
OP0=STAGE.parent/"op0-light-2026-10-31"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def asset(q):
    p=ROOT/q["path"]
    frozen=PARENT/q["path"]
    if frozen.is_file() and sha(frozen)==q["sha256"]:return frozen
    assert sha(p)==q["sha256"],q["path"]
    return p

def verify_parent():
    bound=read(PARENT/"manifest.json")
    for path,digest in bound.items():asset(dict(path=path,sha256=digest))
    report=read(PARENT/"reference/validation/compact-actor-delivery.json")
    assert report["status"]=="scoped_complete_contact_alignment_unroll_acceptance_open"
    assert report["source_controls"]==3034 and report["native_controls"]==53
    assert sha(PARENT/"amiga/out/bruce_amiga.exe")=="4229148ac5b324d8d5296594fd1364439a90550577796b913c1d9e6b559fa561"
    return report

def check_code(elf,name,wanted):
    data,ss=sections(elf)
    _,symbols=elf_symbols(elf)
    sect=dict(ss)[".text"]
    at=symbols[name]-sect[3]
    assert 0<=at<=sect[5]-len(wanted) and data[sect[4]+at:sect[4]+at+len(wanted)]==wanted,(elf,name)

def kernel(obj,name):
    data,headers=sections(obj)
    sec=dict(headers)[".text."+name]
    return data[sec[4]:sec[4]+sec[5]]

def allocated_sections(obj):
    data,headers=sections(obj)
    return {name:(sec[5],data[sec[4]:sec[4]+sec[5]] if sec[1]!=8 else b'')
            for name,sec in headers if sec[2]&2}

def check_run(folder):
    d=read(folder/"identity.json")
    for q in d["source_files"]:asset(q)
    r=dict(l.split("=",1) for l in (folder/"op0-light.txt").read_text().splitlines() if "=" in l)
    assert r==d["run"] and r["restored_os"]==r["finished"]=="1"
    assert r["steps"]==r["warmup_steps"]=="240" and r["source_profile"]=="0"
    assert all(r[k]=="0" for k in ["source_fault","audio_fault","dma_fault"])
    assert int(r["chip_largest_loaded"])>=49152 and int(r["visited_rooms"])==1<<(d["room"]-1)
    active=list(map(int,r["active_loops"].split(",")))
    expected=0 if d["room"]==12 else d["enemy_mask"]
    assert active[expected]==sum(active)==int(r["loops"])
    if d["room"]==12:assert r["climb_steps"]=="240"
    return r

def verify_current():
    parent=verify_parent()
    old=PARENT/"core/c64_rooms.c"
    core=ROOT/"core/c64_rooms.c"
    assert core.read_bytes()==(PILOT/"c64_rooms.c").read_bytes()
    declared="#if defined(__m68k__)\nextern void bl_vic_decode_wide(const unsigned char *, unsigned char *, unsigned long *, unsigned long *);\n#endif\n"
    guarded="""#if defined(__m68k__)
    if(wide && !multi && pointer<=0xffc1){
        bl_vic_decode_wide(m+pointer,raw,out_high,out_low);
        vic_layout[sprite]=2;
        vic_valid|=(unsigned char)(1<<sprite);
        return;
    }
#endif
"""
    text=core.read_text(encoding="utf-8-sig")
    assert text.count(guarded)==text.count(declared)==1
    assert text.replace(declared,"").replace(guarded,"")==old.read_text(encoding="utf-8-sig")
    asm=ROOT/"amiga/vic_wide.s"
    assert asm.read_bytes()==(PILOT/"vic_wide.s").read_bytes()
    before=(PARENT/"amiga-build.ps1").read_text(encoding="utf-8-sig")
    assert (ROOT/"amiga-build.ps1").read_text(encoding="utf-8-sig")==before.replace("'core/source_dma.c')","'core/source_dma.c','amiga/vic_wide.s')")
    # Ordinary parent code/data, input, audio & painter must still match.
    for name,digest in read(PARENT/"manifest.json").items():
        if name.startswith(("core/","amiga/")) and Path(name).suffix in (".s",".c",".h") and name!="core/c64_rooms.c":
            assert sha(ROOT/name)==digest,name
    sys.path.insert(0,str(STAGE))
    from verify_diagnosis import diagnose
    from decode import decode
    diag=read(STAGE/"diagnosis.json")
    assert diagnose()==diag
    assert diag["source_sha256"]==parent["source_sha256"]
    for p,h in diag["artifacts"].items():assert sha(ROOT/p)==h,p
    name="bl_vic_decode_wide"
    wanted=kernel(ROOT/"amiga/out/vic_wide.o",name)
    for obj in ["vic_wide.o","c64_rooms.o"]:
        assert allocated_sections(ROOT/"amiga/out"/obj)==allocated_sections(PILOT/"light"/obj),obj
    assert struct.unpack(">II",(PILOT/"proof/wide-proof.bin").read_bytes())==(512,0)
    for mode in ["light","bare","proof","timed"]:
        for p,h in read(PILOT/mode/"inputs.json").items():asset(dict(path=p,sha256=h))
        check_code(PILOT/mode/"bruce_amiga.elf",name,wanted)
    observed=decode(PILOT/"timed")
    before_trace=diag["traces"]["timed-both-1"]
    before_cold=before_trace["paths"]["pixel_rebuild"]
    after_cold=observed["paths"]["pixel_rebuild"]
    assert before_cold["rebuilds"]==after_cold["rebuilds"]==185
    assert after_cold["cache_lines"]<before_cold["cache_lines"] and observed["missed"]<before_trace["missed"]
    pairs=[]
    paths=[STAGE/"diagnosis.json",PARENT/"manifest.json",PILOT/"proof/wide-proof.bin",PILOT/"timed/op2-fields.bin",
           core,asm,ROOT/"amiga-build.ps1",Path(__file__),ROOT/"tools/test-op2-normal.ps1",ROOT/"docs/OP2_FIELD_AUDIO.md"]
    for left,right in [("op2-reference-both-1","both-1"),("op2-reference-both-2","both-2"),
                       ("op2-reference-bare","both-bare"),("op1-parent-stairs","stairs"),("op1-parent-yamo13","yamo-13")]:
        source=OP0/"runs"/left
        target=PILOT/"runs"/right
        a,b=check_run(source),check_run(target)
        assert (source/"op0-route.bin").read_bytes()==(target/"op0-route.bin").read_bytes()
        check_code(target/"bruce_amiga.elf",name,wanted)
        if right.startswith("both"):
            assert int(b["pal_fields"])<int(a["pal_fields"]) and int(b["audio_missed"])<int(a["audio_missed"])
        else:assert b["audio_missed"]=="0" and int(b["pal_fields"])<=int(a["pal_fields"])
        pairs.append(dict(route=right,fields=[int(r["pal_fields"]) for r in (a,b)],missed=[int(r["audio_missed"]) for r in (a,b)]))
        paths.extend([source/"identity.json",target/"identity.json",target/"op0-light.txt"])
    native=read(ROOT/"reference/validation/source-world-native.json")
    for q in native["build"]+native["source_files"]:
        assert sha(ROOT/q["path"])==q["sha256"],q["path"]
    r=native["run"]
    assert native["status"]=="passed_scoped_native_source_contract" and not native["failures"]
    assert r["source_actor_fixture_cases"]=="53" and r["frames"]=="1200" and int(r["chip_largest_loaded"])>=49152
    assert all(r[k]=="0" for k in ["source_actor_fixture_failure","c64_room_fault","source_dma_faults","source_audio_faults","vic_compare_errors","bad_presents"])
    assert r["restored_os"]=="1"
    assert r["capture_original_hash"]==r["capture_decoded_hash"] and int(r["max_held_image_streak"])<=3
    assert sha(ROOT/"amiga/out/bruce_test.exe")==next(q["sha256"] for q in native["build"] if q["path"].endswith(".exe"))
    fixture=ROOT/next(q["path"] for q in native["build"] if q["path"].endswith(".elf"))
    for elf in [fixture,ROOT/"amiga/out/bruce_amiga.elf"]:
        check_code(elf,name,wanted)
        for symbol in ["bl_vic_equal63","bl_vic_repeat"]:
            check_code(elf,symbol,kernel(PARENT/"amiga/out/vic_compare.o",symbol))
    normal=[ROOT/"amiga/out"/("bruce_amiga."+x) for x in ("exe","elf","adf")]
    normal.append(ROOT/".tmp/amiga-boot/c/start")
    assert sha(normal[0])==sha(normal[3])
    cfg=STAGE/"standalone-adf.uae"
    settings=cfg.read_text(encoding="ascii").splitlines()
    assert "floppy0wp=true" in settings and "floppy0="+str(normal[2]) in settings
    assert not any(line.startswith("filesystem2=") for line in settings)
    paths.append(cfg)
    for mode in ["cli","adf"]:
        p=STAGE/"normal-ui"/mode/"report.json";boot=read(p)
        assert boot["complete_menu"] and boot["elf"]["sha256"]==sha(normal[1])
        if mode=="adf":assert boot["game_states"][-1]["steps"]>boot["game_states"][0]["steps"]
        paths.extend([p,p.parent/"menu.bpl"])
    for label in ["op2-wide-r12","op2-wide-r12-death"]:
        p=ROOT/"reference/analysis/render-coherence-2026-10-29"/label/"report.json";screens=read(p)
        assert screens["elf"]["sha256"]==sha(normal[1]) and screens["snapshots_paused"] and len(screens["samples"])>=12
        assert all(screens[k]==0 for k in ["mixed_phase_samples","max_pixel_mismatch","max_static_pixel_mismatch","max_flicker_illegal_pixels"])
        assert not screens["flicker_stuck_codes"]
        paths.append(p)
    paths.extend([ROOT/"reference/validation/source-world-native.json",PILOT/"fixture/result.json"])
    chain=ROOT/"reference/analysis/actor-chain-2026-10-26"
    for filename in ["report.json","integrated-controls.json"]:
        p=chain/filename
        control=read(p)
        assert control["source_sha256"]==parent["source_sha256"]
        if filename=="report.json":assert control["checks"]==len(control["rows"])==3034
        else:assert len(control["checks"])==5 and control["instructions"]==7055873
        for q in control["source_files"]:assert sha(ROOT/q["path"])==q["sha256"],q["path"]
        paths.append(p)
    for filename,key,count in [("source-vic-host.json","calls",8741),("vic-cache-host.json","cases",25600)]:
        p=ROOT/"reference/validation"/filename
        control=read(p)
        assert control[key]==count
        for q in control["source_files"]:assert sha(ROOT/q["path"])==q["sha256"],q["path"]
        paths.append(p)
    desc=dict(timing_pairs=pairs,decoder_cases=512,decoder_code_and_table_bytes=len(wanted),
              rebuilds=185,rebuild_lines=[before_cold["cache_lines"],after_cold["cache_lines"]],
              fresh_fixtures=53,replay_loops=1200,controlled_missed=int(r["source_clock_missed"]),
              normal_exe_bytes=normal[0].stat().st_size,normal_exe_delta=normal[0].stat().st_size-(PARENT/"amiga/out/bruce_amiga.exe").stat().st_size)
    return dict(parent,date="2026-10-31",status="scoped_complete_op2_wide_vic_decoder_realtime_open",
                op2_wide=desc,largest_chip_block=int(r["chip_largest_loaded"]),normal_build=[item(p) for p in normal],
                artifacts=[item(p) for p in sorted(set(paths))])

if __name__=="__main__":
    if sys.argv[1:]==["--parent"]:
        verify_parent();print("PASS preserved pre-OP2 input hashes")
    else:
        verify_current();print("PASS OP2 wide VIC decoder delivery")
