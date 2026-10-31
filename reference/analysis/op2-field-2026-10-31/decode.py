"""Decode the Amiga's BE32 counters and correlate late polls to completed field calls."""
import argparse
import collections
import json
import struct
from pathlib import Path

HERE=Path(__file__).resolve().parent
KINDS=["no_vic","repeat","no_pair","slow_reuse","pixel_warm","pixel_rebuild"]
OUTCOMES=["same_field","due","late"]
STATS=["calls","vic_lines","vic_max","field_lines","field_max","cache_lines","rebuilds","nested_polls","cache_max"]
EVENT=["pal_offset","step","gap","prev_site","site","prev_origin","origin","prev_phase","phase","prev_tick",
       "kind","field_lines","vic_lines","cache_lines","rebuilds","since_tick_fields","since_tick_field_lines",
       "since_tick_vic_lines","since_tick_cache_lines","previous_tick_observed"]
SITES=["start","game_service_entry","post_field","before_input","after_step","after_paint_prepare",
       "before_actor_draw","blitter_poll","capture_scan","presentation_wait","bitmap_clear"]
ORIGINS=["outer_loop","contact_row","contact_driver","legacy_contact","legacy_tick","sprite_build","translated_contact"]
def text_report(path):
    return dict(line.split("=",1) for line in path.read_text().splitlines() if "=" in line)

def decode(folder):
    r=text_report(folder/"op0-light.txt")
    data=(folder/"op2-fields.bin").read_bytes()
    assert len(data)%4==0
    w=iter(v[0] for v in struct.iter_unpack(">I",data))
    magic,full,fields,ticks,losses,nevents,nested,kinds,results,nstats,words=[next(w) for _ in range(11)]
    assert (magic,kinds,results,nstats,words)==(0x4f503202,len(KINDS),len(OUTCOMES),len(STATS),len(EVENT))
    assert full in (0,1) and nevents<=128
    assert ticks==int(r["audio_ticks"]) and losses==int(r["audio_missed"])
    assert ticks+losses==int(r["pal_fields"]) or abs(ticks+losses-int(r["pal_fields"]))<=1
    assert r["steps"]==r["warmup_steps"]=="240" and r["finished"]==r["restored_os"]=="1"
    assert r["source_fault"]==r["dma_fault"]==r["audio_fault"]=="0"
    stats={}
    for kind in KINDS:
        stats[kind]={}
        for outcome in OUTCOMES:
            row={key:next(w) for key in STATS}
            assert row["cache_lines"]<=row["vic_lines"]<=row["field_lines"]
            assert row["cache_max"]<=row["vic_max"]<=row["field_max"]
            stats[kind][outcome]=row
    all_rows=[row for outcomes in stats.values() for row in outcomes.values()]
    assert sum(row["calls"] for row in all_rows)==fields
    assert sum(row["nested_polls"] for row in all_rows)==nested==0
    events=[]
    histogram=collections.Counter()
    for _ in range(nevents):
        e=dict(zip(EVENT,[next(w) for _ in EVENT]))
        assert e["gap"]>1 and e["step"]<240
        assert e["since_tick_cache_lines"]<=e["since_tick_vic_lines"]<=e["since_tick_field_lines"]
        for key in ("site","prev_site"): e[key]=SITES[e[key]]
        for key in ("origin","prev_origin"): e[key]=ORIGINS[e[key]]
        if e["site"]=="post_field":
            e["kind"]=KINDS[e["kind"]] if full else "untimed"
            assert e["since_tick_fields"]>=1
        else:
            assert e["kind"]==255 and e["vic_lines"]==0 and e["field_lines"]==0
            e["kind"]=None
        histogram[(e["site"],e["origin"])]+=e["gap"]-1
        events.append(e)
    assert next(w,None) is None and sum(e["gap"]-1 for e in events)==losses
    assert sum(outcomes["late"]["calls"] for outcomes in stats.values())==sum(e["site"]=="post_field" for e in events)
    summary={}
    for kind,buckets in stats.items():
        sums={k:sum(row[k] for row in buckets.values()) for k in ["calls","vic_lines","field_lines","rebuilds","cache_lines"]}
        if sums["calls"]:
            summary[kind if full else "untimed"]=dict(**sums,avg_vic_lines=round(sums["vic_lines"]/sums["calls"],2),
                peak_vic_lines=max(row["vic_max"] for row in buckets.values()),late_events=buckets["late"]["calls"])
    return dict(timed=bool(full),fields=fields,pal_fields=int(r["pal_fields"]),audio_ticks=ticks,missed=losses,
                losses_by_site={f"{s}/{o}":n for (s,o),n in histogram.items()},paths=summary,
                counters=stats,events=events,active_loops=r["active_loops"],chip=int(r["chip_largest_loaded"]))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("label");args=p.parse_args()
    result=decode(HERE/"runs"/args.label)
    print(json.dumps({k:v for k,v in result.items() if k not in ("counters","events")},indent=2))
    for e in result["events"][:3]: print(e)

