"""Bind the isolated IRQ implementation, original-byte controls and m68000 probe."""
import argparse,hashlib,json
from pathlib import Path
from audit_vic_native_kernels import sections
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/irq-input-2026-10-30'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def verify():
    host=read(BASE+'/irq-context-candidate.json')
    assert host['cases']==3352 and host['instructions']==479308
    assert host['all_ram_and_registers'] and host['returned_pc_verified'] and host['sid_gate_edges_verified']
    assert set(host['handlers'])=={'0x48c1','0x491e','0x4982','0x14a4','0x1574'}
    assert set(host['commands'])==set(map(str,range(8)))
    for e in host['artifacts']:assert item(e['path'])==e,e['path']
    assert not host['production_changed'] and not host['original_raster_phase_verified']
    rows=[]
    for label in ['before','candidate']:
        p=BASE+'/compiler/'+label+'.o';_,ss=sections(ROOT/p);sums={}
        for name,q in ss:
            if not q[2]&2:continue
            kind=next((n for n in ['.text','.rodata','.data','.bss'] if name==n or name.startswith(n+'.')),None)
            if kind:sums[kind]=sums.get(kind,0)+q[5]
        stack=[];sp=BASE+'/compiler/'+label+'.su'
        for line in (ROOT/sp).read_text(encoding='utf-8-sig').splitlines():
            head,amount,kind=line.split('\t');name=head.rsplit(':',1)[-1]
            if name in ['actor_code','source_actor_field','audio_driver'] or name.startswith(('irq_context','bl_irq_context')):
                stack.append(dict(function=name,local_bytes=int(amount),classification=kind))
        rows.append(dict(object=item(p),sections=sums,stack_file=item(sp),selected_stack_frames=stack))
    assert rows[1]['sections']['.bss']-rows[0]['sections']['.bss']==2
    normal=read('reference/validation/source-world-delivery.json')['normal_build']
    for e in normal:assert item(e['path'])==e
    assert item('.tmp/amiga-boot/c/start')['sha256']==next(e['sha256'] for e in normal if e['path'].endswith('.exe'))
    paths=[BASE+'/irq-context-candidate.json',BASE+'/game-irq-disassembly.txt','tools/audit_irq_context_candidate.py','docs/IRQ_CONTEXT_CANDIDATE.md']
    paths += [e['path'] for e in host['artifacts']]
    return dict(status='verified_isolated_irq_context_candidate',production_changed=False,source_cases=3352,source_instructions=479308,
        compiler_flags=['-m68000','-Os','-g','-nostdlib','-ffreestanding','-fno-builtin','-fno-tree-loop-distribute-patterns','-fomit-frame-pointer','-ffunction-sections','-fdata-sections','-mshort','-DBL_AUTOTEST=0','-fstack-usage'],
        compiler_builds=rows,normal_build=normal,full_stack_high_water_verified=False,realtime_accepted=False,natural_playthrough=False,
        limits=['Unlinked object includes public test bridge, not a normal HUNK footprint','Compiler stack values are local frames, not maximum whole-call-chain use','Host source proof; candidate has not executed in a native Amiga test','Explicit PC/pin/raster fixtures, not original interrupt timing; title/$152C music state remains open'],artifacts=[item(p) for p in sorted(set(paths))])
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();r=verify();path=BASE+'/irq-context-binding.json'
    if a.record:(ROOT/path).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    else:assert read(path)==r
    print('PASS isolated IRQ context: 3352 all-RAM/register/PC/SID-gate controls; m68000 frame/size probe; normal build unchanged')
if __name__=='__main__':main()
