"""Verify the R01 Kage fix independently from the still-open whole-game timing gate."""
import json
import struct
from pathlib import Path
from verify_score_display_delivery import item,decimal_sections

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/"reference/analysis/kage-paula-2026-11-01"

def read(path):return json.loads(path.read_text(encoding="utf-8-sig"))
def checked(entry):
    path=ROOT/entry["path"]
    assert item(path)==entry,path
    return path

def verify_current():
    manifest=STAGE/"delivery.json";data=read(manifest)
    child=STAGE.parent/"field-work-2026-11-01/delivery.json"
    if child.is_file():
        successor=read(child)
        assert checked(successor["predecessor"])==manifest
        # The combat/input forks below belong to the earlier delivery. The
        # successor supplies fresh field, controller, render and normal runs.
        data=dict(data,**successor)
    draw_manifest=STAGE.parent/"actor-draw-2026-11-01/delivery.json"
    if draw_manifest.is_file():
        draw=read(draw_manifest)
        assert checked(draw["predecessor"])==child
        parent_fields=data["field_evidence"]
        data=dict(data,**draw)
        data["field_evidence"]={**parent_fields,**draw["field_evidence"]}
    four_manifest=STAGE.parent/"four-work-2026-11-01/delivery.json"
    if four_manifest.is_file():
        four=read(four_manifest)
        assert checked(four["predecessor"])==draw_manifest
        prior_fields=data["field_evidence"]
        data=dict(data,**four)
        data["field_evidence"]={**prior_fields,**four["field_evidence"]}
    parent=read(checked(data["parent"]))
    previous=read(STAGE/"previous-delivery.json")
    assert previous["normal_build"]==parent["normal_build"]
    for ref in parent["normal_build"][:3]:
        archived=STAGE.parent/"op-finish-2026-10-31/release"/Path(ref["path"]).name
        assert item(archived)["sha256"]==ref["sha256"]
    for entry in data["normal_build"]+data["proofs"]:checked(entry)
    assert data["normal_build"][0]["sha256"]==data["normal_build"][3]["sha256"]
    assert decimal_sections(ROOT/"amiga/out/c64_rooms.o")==data["engine_sections"]
    original=read(checked(data["cpu"]))
    assert (original["cases"],original["full_combats"],original["source_extra_lives"])==(124,2,55)
    assert struct.unpack(">III",checked(data["native"]).read_bytes())==(124,0,1)
    comparison=read(checked(data["comparison"]))
    for witness in data["witness"].values():
        assert "finished=1" in checked(witness["raw"]).read_text()
    for step,score,health in ((168,[425,6975],[2,123]),(207,[6975,13525],[3,124])):
        c64=comparison["vice"][f"match{step}"]
        assert c64["source"]==original["frozen_sha256"] and c64["same_right_replay"]
        assert (c64["awards"],c64["reentries"],c64["raster_game_irqs"])==(53,26,9)
        assert c64["score"]==score and [c64["begin"][2],c64["end"][2]]==health
        for mode in ("response","response-old","production"):
            branch=comparison["amiga"][f"{mode}-{step}"]
            assert branch["health"]==health and branch["score"]==score
            assert branch["first_distinct_bruce_lines"] and min(branch["first_joystick_slot_lines"])>0
    play=comparison["vice"]["play"]
    assert (play["begin"][2],play["end"][2],play["awards"],play["reentries"])==(0,126,51,25)
    assert play["score"]==[475,6775] and play["same_right_replay"]
    for mode,entry in data["ui"].items():
        ui=read(checked(entry))
        assert ui["normal_exe_sha256"]==data["normal_build"][0]["sha256"]
        assert ui["complete_menu"] and ui["pause_preserved"] and ui["fields"]>=6000 and not ui["after"]["fault"]
        assert all(0<v<0x80000 for v in ui["dma"].values())
        assert all(0xc00000<=s["base"]<s["base"]+s["bytes"]<=0xc80000 for s in ui["layout"])
        if mode=="cli":assert ui["joystick_crossings"]==[2,1]
        else:assert mode=="adf" and ui["turn_after_death"]["player"]==2
    runs={}
    for label,rec in data["runs"].items():
        rows=dict(line.split("=",1) for line in checked(rec["raw"]).read_text().splitlines() if "=" in line)
        assert rows["finished"]==rows["restored_os"]=="1"
        assert all(int(rows[k])==0 for k in ("audio_fault","source_fault","dma_fault","source_profile"))
        runs[label]=rows
    passed=0
    for label,rec in data["runs"].items():
        if rec["exe"]!=data["diagnostic_exe"] or rec["route"]!="0003020000f000f0":continue
        v=runs[label]
        assert int(v["steps"])==240 and 0<int(v["pal_fields"])<=821
        assert int(v["paula_publications"])==int(v["pal_fields"])
        assert all(v[k]=="0" for k in ("audio_missed","paula_empty","paula_double"))
        assert [int(n) for n in v["active_loops"].split(",")]==[0,0,0,int(v["loops"])]
        passed+=1
    assert passed>=2
    world=read(ROOT/"reference/validation/source-world-native.json")
    for entry in world["source_files"]+world["build"]:checked(entry)
    assert not world["failures"] and world["run"]["source_actor_fixture_cases"]=="53" and world["run"]["frames"]=="1200"
    controls=read(ROOT/"reference/analysis/actor-chain-2026-10-26/report.json")
    integrated=read(ROOT/"reference/analysis/actor-chain-2026-10-26/integrated-controls.json")
    for proof in (controls,integrated):
        for entry in proof["source_files"]:checked(entry)
    assert controls["checks"]==3034 and len(integrated["checks"])==5
    domains={"source-score-host":("checks",2852),"source-vic-host":("calls",8741),
        "source-audio-host":("source_cpu_fields_compared",7540),"source-dma-host":("channel_images",4554),
        "source-contact-host":("checks",4239),"source-sprite-copy-host":("checks",1536),
        "source-object-host":("checks",65536),"source-visibility-host":("checks",768),
        "vic-cache-host":("cases",25600),"view-mask-host":("cases",2293920),"source-paint-host":("cases",6)}
    domain_files=[]
    for name,(metric,count) in domains.items():
        path=ROOT/f"reference/validation/{name}.json"
        proof=read(path)
        for entry in proof["source_files"]:checked(entry)
        value=proof[metric]
        assert (len(value) if isinstance(value,list) else value)==count,name
        domain_files.append(item(path))
    mode=data["production_mode"]
    long_runs=[runs[f"long-{mode}-{suffix}"] for suffix in ("a","b")]
    assert all(int(v["pal_fields"])>=6000 for v in long_runs)
    measured=long_runs+[runs[label] for label,rec in data["runs"].items() if rec["exe"]==data["diagnostic_exe"]]
    cadence=all(abs(int(v["pal_fields"])-3*int(v["steps"]))<=2 and
                all(v[field]=="0" for field in ("audio_missed","paula_empty","paula_double")) for v in measured)
    report=dict(previous,date="2026-11-01",status="r01_two_kage_contacts_continuous_paula",source_sha256=original["frozen_sha256"],
        normal_build=data["normal_build"],realtime_gate_passed=cadence and world["realtime_contract_passed"],edition_verified=False,natural_playthrough=False,
        full_original_parity=False,largest_chip_block=int(world["run"]["chip_largest_loaded"]),native_controls=53,
        op_measured={n:[int(v["steps"]),int(v["pal_fields"]),int(v["paula_empty"])] for n,v in runs.items()},
        open_gates=["Three fields per ordinary step throughout combat","Natural IRQ, input and whole-game timing","Untouched 1984 edition and full playthrough"],
        kage_fall=passed,artifacts=[item(manifest),item(STAGE/"previous-delivery.json"),*data["proofs"],*domain_files,data["comparison"],data["cpu"],data["native"],*data["ui"].values()])
    if child.is_file():
        evidence={name:checked(e) for name,e in data["field_evidence"].items()}
        assert decimal_sections(ROOT/"amiga/out/source_dma.o")==data["dma_sections"]
        for name,checks in (("native-fall-proof/proof.bin",246),("dma-proof/proof.bin",128),("ports-confirm/ports.bin",12)):
            assert struct.unpack(">III",evidence[name].read_bytes())==(checks,0,1)
        fold=read(evidence["fall-proof/result.json"])
        assert fold["frozen_sha256"]==original["frozen_sha256"] and fold["source_instructions"]==4050583
        assert fold["cases"]==246 and fold["ram_bytes"]==65536 and fold["registers"]==10 and fold["source_extra_lives"]==110
        assert "hit=728,102403,1,124,1392" in evidence["long-hits-a/op0-light.txt"].read_text().splitlines()
        failed=read(evidence["alloc-replay/allocation.json"])
        fixed=read(evidence["alloc-release/allocation.json"])
        assert failed["hunks"][".bss"]<0x80000 and failed["allocations"]["buffers"]==[0,0] and failed["allocations"]["sfx_pcm"]==0
        assert fixed["original_sha256"]==world["build"][0]["sha256"]
        assert 0xc00000<=fixed["hunks"][".bss"]<0xc80000
        for name in ("buffers","copper","room_slots","sfx_pcm","fighter_dma","tile_dma"):
            addresses=fixed["allocations"][name]
            assert all(0<address<0x80000 for address in (addresses if isinstance(addresses,list) else [addresses]))
        slot=read(ROOT/"reference/validation/source-input-slot.json")
        assert slot["production_enabled"] and slot["cases"]==99072 and slot["all_ram_and_registers"]
        for entry in slot["artifacts"]:checked(entry)
        inputs=read(evidence["input-proof.json"])
        assert (inputs["cases"],inputs["slot_reads"],inputs["retained"])==(32768,16384,16384)
        assert inputs["source_sha256"]==fold["frozen_sha256"]
        phases=read(evidence["vice-slots.json"])
        assert phases["source_sha256"]==original["frozen_sha256"]
        for state in ("ground","air"):
            assert [s["direction"] for s in phases["cases"][state]["before"]]==[7,7,7]
            assert [s["direction"] for s in phases["cases"][state]["after"]]==[15,7,7]
        for scene,count in (("stairs",36),("death",12)):
            v=read(evidence[scene])
            assert v["elf"]["sha256"]==item(ROOT/"amiga/out/bruce_amiga.elf")["sha256"]
            assert len(v["samples"])==count and not any(v[k] for k in ("mixed_phase_samples","max_static_pixel_mismatch","max_flicker_illegal_pixels","flicker_stuck_codes"))
            if scene=="death":assert v["room_roundtrip"] and v["controlled_death"]["loader_epoch_after"]!=v["controlled_death"]["loader_epoch_before"]
        report.update(status="three_field_work_areas_measured",field_work=mode,source_instructions=integrated["instructions"])
        report["audio_by_route"]={name:{key:int(row[key]) for key in
            ("pal_fields","audio_missed","paula_publications","paula_empty","paula_double")} for name,row in runs.items()}
        report["continuous_long_audio"]=all(v["pal_fields"]==v["paula_publications"] and
            all(v[k]=="0" for k in ("audio_missed","paula_empty","paula_double")) for v in long_runs)
        report["artifacts"]+=[item(child),*data["field_evidence"].values()]
    if draw_manifest.is_file():
        previous_draw=read(child)
        prior_world=read(checked(draw["prior_replay"]))
        assert draw["prior_replay"]["sha256"]==next(r["sha256"] for r in previous_draw["proofs"]
                                                     if r["path"]=="reference/validation/source-world-native.json")
        for name in ("direct-a","direct-b"):
            before=previous_draw["runs"][name.replace("direct","release")]
            old=dict(l.split("=",1) for l in checked(before["raw"]).read_text().splitlines() if "=" in l)
            assert runs[name]["climb_steps"]==old["climb_steps"] and runs[name]["air_steps"]==old["air_steps"]
            assert int(runs[name]["pal_fields"])<int(old["pal_fields"])
        for name in ("direct-still-a","direct-still-b"):
            assert runs[name]["steps"]=="240" and int(runs[name]["pal_fields"])<=743
        assert report["continuous_long_audio"]
        assert all(v["audio_missed"]==v["paula_empty"]==v["paula_double"]==0 for v in report["audio_by_route"].values())
        profile=checked(draw["profile"]).read_text().splitlines()
        assert sum(line.startswith("view=") for line in profile)==4
        assert "finished=1" in checked(draw["interpolation_only"]).read_text().splitlines()
        seams=read(checked(draw["audio_seams"]))
        assert seams["source_sha256"]==original["frozen_sha256"]
        assert seams["ram_bytes"]==65536 and seams["registers_and_latches"]==13
        assert sum(r["fields"] for r in seams["comparisons"])==2880
        assert sum(r["polls"] for r in seams["comparisons"])==3468
        assert world["run"]["capture_original_hash"]==world["run"]["capture_decoded_hash"]==prior_world["run"]["capture_original_hash"]
        assert draw["image_bytes"]==40960 and draw["image_sha256"]=="1391230165f1c6fd5232e88423c816def89ffdf8586a9c93588e431d1a9ccfe6"
        assert any(l.startswith("miss=2,1808,2,") for l in checked(draw["traced_miss"]).read_text().splitlines())
        for raw in draw["without_audio_checks"]:
            assert "paula_empty=3" in checked(raw).read_text().splitlines()
        report.update(status="direct_actor_drawing_measured",actor_draw=True)
        report["artifacts"] += [item(draw_manifest),draw["prior_replay"],draw["profile"],draw["interpolation_only"],
                                draw["audio_seams"],draw["traced_miss"],*draw["without_audio_checks"]]
    if four_manifest.is_file():
        controls={k:checked(v) for k,v in four["controls"].items()}
        lamps=read(controls["lamps"])
        assert lamps==dict(checks=303,steps=259,jumps=42,deaths=3,switches=2,masks_per_check=20)
        assert read(controls["queue"])==dict(passes=9216,budget_stops=6204,empty_passes=1252)
        assert struct.unpack(">HH",controls["rows"].read_bytes())==(192,0)
        timings=list(struct.iter_unpack(">4I",controls["timings"].read_bytes()))
        assert len(timings)==9 and all(new1+new2<old1+old2 for old1,new1,new2,old2 in timings)
        for name,expected in four["modules"].items():
            assert decimal_sections(ROOT/("amiga/out/"+name+".o"))==expected,name
        for name in ("direct-a","direct-b"):
            old=checked(draw["runs"][name]["raw"]).read_text().splitlines()
            assert int(runs[name]["pal_fields"])<int(next(l[11:] for l in old if l.startswith("pal_fields=")))
        report.update(status="measured_lamp_background_and_contact_updates",four_work=True)
        report["artifacts"]+=[item(four_manifest),*four["controls"].values()]
    return report
