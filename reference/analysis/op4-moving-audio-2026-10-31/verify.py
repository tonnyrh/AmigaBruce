"""Check the two loss windows, the actual C64 branches and the new IRQ witness."""
from collections import Counter
from pathlib import Path
import argparse,hashlib,json,shutil,struct
from decode import decode,report
from audit_combat import audit,ROOT,sha
HERE=Path(__file__).resolve().parent
WORK=ROOT/".tmp/op4-moving"
DATA=HERE/"runs"
TRACES=("sites-move","timed-move1","timed-move2","timed-still")
ROUTES=("move-control1","move-control2",*TRACES,"move-focus","move-trial1","move-trial2","still-trial")
def load(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def digest(p):return sha(p.read_bytes())
def read_focus(p):
    b=p.read_bytes();n,k=struct.unpack_from(">II",b)
    assert n<=8 and k<=16 and len(b)==8+n*36+k*12
    names="step combat_lines awards award_lines decimal_lines back_edges peak_award_lines last_actor score".split()
    return ([dict(zip(names,struct.unpack_from(">9I",b,8+36*i))) for i in range(n)],
            [dict(zip(("step","gap","phase"),struct.unpack_from(">3I",b,8+36*n+12*i))) for i in range(k)])
def check(record=False):
    old=load(HERE.parent/"op2-vic-pairs-2026-10-31/measurements.json")
    for q in old["normal_build"]+old["inputs"]:assert digest(ROOT/q["path"])==q["sha256"],q["path"]
    frozen=(ROOT/".reference/c64/work/untrained-memory.bin").read_bytes()
    assert sha(frozen)==old["c64_sha256"]
    for at,h in ((0x2bf9,"b5bc2910"),(0x2c0e,"38e905"),(0x2c51,"4cf92b"),(0x4915,"20a815"),(0x15af,"2003eb2073ef2073f0"),(0x169d,"ad0401f061")):
        assert frozen[at:at+len(bytes.fromhex(h))].hex()==h,hex(at)
    if record:
        for name in ROUTES:
            src=WORK/name;dst=DATA/name;dst.mkdir(parents=True,exist_ok=True)
            for f in ["op0-light.txt"]+(["op4-audio.bin"] if name in TRACES else ["focus.bin"] if name=="move-focus" else []):
                shutil.copyfile(src/f,dst/f)
        for name in ("combat168","combat207"):
            r=audit(WORK/name);(DATA/(name+".json")).write_text(json.dumps(r,indent=2)+"\n")
        shutil.copyfile(WORK/"irq.json",DATA/"irq.json")
        shutil.copyfile(WORK/"irq-native/proof.bin",DATA/"irq-proof.bin")
    refs={}
    for name in ROUTES:
        r=report(DATA/name/"op0-light.txt")
        for key,expected in dict(room=1,enemy_mask=3,warmup_steps=240,steps=240,source_fault=0,
                dma_fault=0,audio_fault=0,source_profile=0,visited_rooms=1,restored_os=1,finished=1).items():
            assert int(r[key])==expected,(name,key)
        assert r["active_loops"]=="0,0,0,240" and int(r["chip_largest_loaded"])>=49152
        assert abs(int(r["audio_ticks"])+int(r["audio_missed"])-int(r["pal_fields"]))<=1
        still=name in ("timed-still","still-trial")
        assert int(r["input_route"])==(0 if still else 2)
        assert int(r["air_steps"])==(0 if still else 96)
        refs[name]=dict(fields=int(r["pal_fields"]),ticks=int(r["audio_ticks"]),missed=int(r["audio_missed"]))
    assert all(refs[n]["missed"]==12 for n in ("move-control1","move-control2"))
    assert all(refs[n]["missed"]==0 for n in ("move-trial1","move-trial2","timed-still","still-trial"))
    traces={n:decode(DATA/n) for n in TRACES}
    for n,d in traces.items():
        big=[e for e in d["events"] if e["gap"]>=5]
        if n=="timed-still":assert not d["events"];continue
        assert [e["step"] for e in big]==[168,207]
        for e in big:
            assert e["previous_poll"].endswith("/contact_row") and e["late_poll"]=="game_entry/source_sprite"
            if d["timed"]:assert e["previous_poll_work"]["combat"]>=2000 and e["previous_poll_work"]["combat"]>e["previous_poll_lines"]*.85
    focus,late=read_focus(DATA/"move-focus/focus.bin")
    assert sum(e["gap"]-1 for e in late)==refs["move-focus"]["missed"]
    assert [e["step"] for e in focus]==[168,207]
    assert all(e["awards"]==53 and e["back_edges"]==26 and e["decimal_lines"]<=e["award_lines"]<=e["combat_lines"] for e in focus)
    source=[]
    for n in ("combat168","combat207"):
        d=load(DATA/(n+".json"))
        local=ROOT/".reference/c64/work"/HERE.name/n
        if (local/"combat.bin").exists():assert json.loads(json.dumps(audit(local)))==d
        assert all(v["ram_matches"] and v["registers_match"] and v["masked_instructions"]==0 for v in d["variants"])
        v=d["variants"][0]
        assert len(v["kill_reentries"])==26 and all(x==2 and flags==144 and not irq for x,flags,health,irq in v["kill_reentries"])
        assert len(v["score_calls"])==53 and v["score_after"]-v["score_before"]==6550
        source.append(dict(capture=n,instructions=v["instructions"],cycles=v["source_cycles"],health_before=v["health_before"][2],
                           health_after=v["health_after"][2],score_before=v["score_before"],score_after=v["score_after"]))
    irq=load(DATA/"irq.json");assert len(irq)==6 and struct.unpack(">III",(DATA/"irq-proof.bin").read_bytes())==(6,0,1)
    for q in irq:
        assert q["caller_restored"] and q["isolated_context_exact"] and q["pc"]=="2c51" and q["i"]==q["decimal"]==0
        assert len(q["existing_seam_diffs"])==38 and q["original_continuation"]==q["existing_continuation"]
    result=dict(status="moving_audio_loss_traced_checkpoint_trial_not_promoted",source_sha256=sha(frozen),
                trials=refs,traces=traces,focused_combat=focus,focused_losses=late,source_calls=source,
                irq_context=dict(cases=len(irq),runtime_different_bytes=38,contexts_exact_on_68000=6),
                normal_build=old["normal_build"],production_changed=False,natural_playthrough=False,
                original_raster_phase_verified=False,original_edition_verified=False,
                raw={p.relative_to(DATA).as_posix():digest(p) for p in sorted(DATA.rglob("*")) if p.is_file()},
                inputs={p.name:digest(p) for p in sorted(HERE.iterdir()) if p.suffix in (".py",".h",".ps1")})
    if record:
        binaries={name:digest(WORK/name/"bruce_amiga.exe") for name in (*ROUTES,"combat168","combat207","irq-native")}
        assert binaries["move-control1"]==binaries["move-control2"]==load(HERE.parent/"op1-kage-prefix-2026-10-31/result.json")["builds"]["executables"]["moving-before"]
        assert binaries["move-trial1"]==binaries["move-trial2"]==binaries["still-trial"]
        result["tested_binaries"]=binaries
        (HERE/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    else:
        saved=load(HERE/"result.json");saved.pop("tested_binaries");assert saved==result
    print("PASS OP4 moving route, source combat and IRQ controls;",[(n,r["fields"],r["missed"]) for n,r in refs.items()])
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--record",action="store_true");check(p.parse_args().record)

