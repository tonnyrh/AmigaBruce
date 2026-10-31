"""Bind lightweight normal-path measurements; do not certify game parity or FPS."""
import argparse,hashlib,json,math
from pathlib import Path
from summarize_source_performance import NAMES,interval
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/op0-light-2026-10-31'
TARGET='reference/validation/op0-light.json'
LABELS=['r01-bruce-r01','r01-yamo-r01','r01-kage-r01','r01-both-r02',
        'r01-both-r03','r01-both-profile-r01','r12-stairs-r01','r13-yamo-r01','r01-both-bare-r01']
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def check(q):assert item(q['path'])['sha256']==q['sha256'],q['path']

def verify():
    assert item('.reference/c64/work/untrained-memory.bin')['sha256']==SHA
    assert item('amiga/out/bruce_amiga.exe')['sha256']=='4229148ac5b324d8d5296594fd1364439a90550577796b913c1d9e6b559fa561'
    paths={'tools/build_light_op0_probe.py','tools/build_bare_op0_probe.py','tools/verify_light_op0.py',
      'tools/test-light-op0.ps1','tools/test-bare-op0.ps1','docs/OP0_LIGHT_MEASUREMENTS.md'}
    result=[];profile=[];identical=[]
    for label in LABELS:
        folder=BASE+'/runs/'+label;d=read(folder+'/identity.json');r=d['run']
        assert d['autotest'] is False and not d['natural_playthrough'] and not d['realtime_accepted']
        assert d['warmup']==d['steps']==240 and r['steps']=='240'
        assert r['restored_os']==r['finished']=='1'
        assert r['source_fault']==r['dma_fault']==r['audio_fault']=='0'
        assert int(r['chip_largest_loaded'])>=49152
        assert int(r['visited_rooms'])==1<<(d['room']-1)
        for e in d['source_files']:check(e);paths.add(e['path'])
        raw=dict(l.split('=',1) for l in (ROOT/folder/'op0-light.txt').read_text().splitlines() if '=' in l)
        assert raw==r
        paths.update([folder+'/identity.json',folder+'/op0-light.txt',folder+'/a500.uae'])
        cfg=(ROOT/folder/'a500.uae').read_text()
        for setting in ['cpu_model=68000','cpu_speed=real','cpu_cycle_exact=true',
                        'chipset=ocs','chipmem_size=1','bogomem_size=2','fastmem_size=0']:
            assert setting in cfg,(label,setting)
        active=list(map(int,r['active_loops'].split(',')));assert sum(active)==int(r['loops'])
        expected_active=0 if d['room']==12 else d['enemy_mask']
        assert active[expected_active]==int(r['loops']),(label,active)
        quantiles={};bins=list(map(int,r['step_bins'].split(',')))
        if d['variant']!='bare':
            assert sum(bins)==240
            for q in [50,95,99]:
                n=0
                for i,count in enumerate(bins):
                    n+=count
                    if n>=math.ceil(q*240/100):quantiles[str(q)]=interval(i);break
        if d['variant']=='profile':
            assert r['perf_errors']=='0'
            for i,name in enumerate(NAMES):
                calls,total,own,maximum,context,*hist=map(int,r['perf_'+str(i)].split(','))
                assert calls==sum(hist) and own<=total
                profile.append(dict(name=name,calls=calls,inclusive_lines=total,exclusive_lines=own,
                  exclusive_lines_per_source_step=round(own/240,3),max_inclusive=maximum))
        result.append(dict(label=label,variant=d['variant'],room=d['room'],enemy_mask=d['enemy_mask'],
          steps=240,loops=int(r['loops']),pal_fields=int(r['pal_fields']),pal_lines=int(r['pal_lines']),
          fields_per_step=round(int(r['pal_fields'])/240,4),audio_missed=int(r['audio_missed']),
          work_lines=int(r['work_lines']),wait_lines=int(r['wait_lines']),
          boundary_and_counter_lines=(int(r['pal_lines'])-int(r['work_lines'])-int(r['wait_lines'])) if d['variant']!='bare' else None,
          active_loops=active,climb_steps=int(r['climb_steps']),step_line_quantile_intervals=quantiles,
          largest_chip=int(r['chip_largest_loaded']),largest_slow=int(r['slow_largest_loaded'])))
    # Actual objects, not a claim that two linked programs have identical addresses.
    for p in sorted((ROOT/'amiga/out').glob('*.o')):
        candidate=ROOT/BASE/'light/out'/p.name
        if p.name=='main.o' or not candidate.exists():continue
        assert p.read_bytes()==candidate.read_bytes(),p.name
        identical.append(p.name);paths.add(p.relative_to(ROOT).as_posix());paths.add(candidate.relative_to(ROOT).as_posix())
    assert {'c64_rooms.o','source_audio.o','source_dma.o','session.o','runtime.o'}<=set(identical)
    assert next(r for r in result if r['room']==12)['climb_steps']==240
    rows={r['label']:r for r in result}
    near=rows['r01-both-bare-r01']['pal_fields'];full=rows['r01-both-r02']['pal_fields']
    assert abs(rows['r01-both-r03']['pal_fields']-full)<=4
    contact=sum(r['exclusive_lines'] for r in profile if r['name'] in ['contact','rows','align'])
    return dict(date='2026-10-31',status='passed_scoped_op0_diagnosis',production_changed=False,
      source_sha256=SHA,edition_verified=False,natural_playthrough=False,realtime_gate_passed=False,
      measurements=result,profile=profile,identical_non_main_objects=identical,
      timer_control=dict(minimal_fields=near,detailed_fields=full,
        added_percent=round((full/near-1)*100,3),not_zero_overhead=True),
      selected_next_target=dict(op='OP1',source_range='$537E-$53E3 within $5212-$55AA',
        native_scope='source_contact_scan batch setup and existing bl_contact_rows8; preserve ordered lanes, aliases and original eight-row service boundaries',
        evidence='Largest measured contact sub-block; contact/rows/align exclusive sum excludes nested field/audio service',
        profiled_contact_exclusive_lines_per_step=round(contact/240,3),
        expected_gain='Unmeasured; existing native kernel must be inspected, not treated as untranslated code'),
      limits=['Diagnostic invincibility/infinite lives, room selection, scripted input and optional enemy removal, not natural play',
        'CPU object code matches normal build; instrumented main and linked addresses differ',
        'Minimal timer control is still instrumented; profile changes field count and route phase',
        'Short 240-step runs, not the two 6000-field final acceptance runs',
        'R13 route does not resolve natural respawn pressure after defeat',
        'No physical A500, raster/input parity, stack-margin or new game-behaviour acceptance'],
      artifacts=[item(p) for p in sorted(paths)])

def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args();r=verify()
    if args.record:(ROOT/TARGET).write_text(json.dumps(r,indent=2)+'\n')
    else:assert read(TARGET)==r,'Evidence changed; inspect before recording'
    for q in r['measurements']:print(q['label'],q['pal_fields'],q['fields_per_step'],q['audio_missed'])
    print('PASS OP0: normal objects unchanged; next target OP1 contact rows; real-time acceptance open')

if __name__=='__main__':main()
