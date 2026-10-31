"""A bounded assembly-only optimization, preserving preceding delivery proof."""
import hashlib,json,os
from pathlib import Path
from build_contact_unroll_probe import candidate
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/contact-unroll-2026-10-31'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def enabled():
    p=ROOT/BASE/'baseline/contact_align.s'
    return p.exists() and (ROOT/'amiga/contact_align.s').read_text()==candidate(p.read_text(),True,False)
class FrozenView:
    def __init__(self,entries):self.files={e['path']:ROOT/BASE/'parent'/e['path'] for e in entries}
    def __fspath__(self):return os.fspath(ROOT)
    def __truediv__(self,p):return self.files.get(Path(p).as_posix(),ROOT/p)
def verify_parent():
    import verify_loader_blank_delivery as loader
    import verify_compact_actor_delivery as compact
    manifest=read(BASE+'/parent/manifest.json')
    for e in manifest['files']:assert item(BASE+'/parent/'+e['path'])['sha256']==e['sha256'],e['path']
    oldroot=loader.ROOT;flag=getattr(compact,'_contact_parent_replay',False)
    olddump=loader.subprocess.check_output
    def historical_dump(args,**kwargs):
        result=olddump(args,**kwargs)
        # objdump prints its input filename above the machine instructions.
        # Replaying a frozen ELF changes that heading only; preserve the
        # exact recorded heading, without changing any disassembly bytes.
        if isinstance(result,str):
            result=result.replace(str(ROOT/BASE/'parent/amiga/out/bruce_amiga.elf'),str(ROOT/'amiga/out/bruce_amiga.elf'))
        return result
    try:
        loader.ROOT=FrozenView(manifest['files']);compact._contact_parent_replay=True;loader.subprocess.check_output=historical_dump
        report=loader.verify_current()
        assert report==read(BASE+'/parent/verified-report.json')
    finally:loader.ROOT=oldroot;compact._contact_parent_replay=flag;loader.subprocess.check_output=olddump
    return report

def verify_current():
    assert enabled();parent=verify_parent()
    frozen=read(BASE+'/parent/manifest.json');expected={e['path']:e['sha256'] for e in frozen['files']}
    # Main, all C code, other assembly, assets, build flags and generated
    # programs stay byte-identical. Only this alignment helper changes.
    for p,sha in expected.items():
        if (p.startswith('core/') or p.startswith('amiga/')) and Path(p).suffix in ['.c','.h','.s'] and p!='amiga/contact_align.s':assert item(p)['sha256']==sha,p
    assert item('amiga-build.ps1')['sha256']==expected['amiga-build.ps1']
    from verify_contact_unroll_experiment import verify as trial
    experiment=trial();selected=experiment['rows'][-1];before=experiment['rows'][0]
    assert selected['variant']=='candidate-compact' and selected['missed_audio_ticks']==0
    assert selected['pal_fields']<before['pal_fields'] and selected['stationary'][3][1]<before['stationary'][3][1]
    paths=[BASE+'/parent/manifest.json',BASE+'/parent/verified-report.json',BASE+'/report.json','tools/verify_contact_unroll_delivery.py','tools/freeze_contact_unroll_parent.py','tools/verify_compact_actor_delivery.py','tools/verify_source_optimization.py','amiga/contact_align.s','docs/CONTACT_UNROLL_OPTIMIZATION.md']
    native=read('reference/validation/source-world-native.json');r=native['run']
    assert native['status']=='passed_scoped_native_source_contract' and not native['failures'] and native['contact_reference_separate']
    assert r['source_actor_fixture_cases']=='53' and r['frames']=='1200' and r['restored_os']=='1'
    assert int(r['chip_largest_loaded'])>=49152 and int(r['max_held_image_streak'])<=3
    for k in ['source_actor_fixture_failure','c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','c64_render_mismatches','capture_fault','vic_compare_errors','bad_presents']:assert r[k]=='0',k
    assert r['capture_original_hash']==r['capture_decoded_hash']
    for e in native['source_files']+native['build']:assert item(e['path'])['sha256']==e['sha256'];paths.append(e['path'])
    paths.append('reference/validation/source-world-native.json')
    from audit_contact_kernel_images import verify as contact
    perf='reference/analysis/optimization-2026-10-27/contact-unroll-compact-r01/bruce_test.elf'
    kernels=contact(['amiga/out/bruce_amiga.elf',next(e['path'] for e in native['build'] if e['path'].endswith('.elf')),perf])
    p=BASE+'/delivery-kernels.json';assert read(p)==kernels;paths.append(p)
    # Unchanged helpers are also compared to the actual prior normal build.
    from audit_vic_native_kernels import sections
    from capture_paula_stream import elf_symbols
    parentelf=BASE+'/parent/amiga/out/bruce_amiga.elf'
    raw,ss=sections(ROOT/parentelf);_,oldsyms=elf_symbols(ROOT/parentelf)
    for path in [p['path'] for p in kernels['builds']]:
        data,secs=sections(ROOT/path);_,syms=elf_symbols(ROOT/path)
        for name in ['bl_sprite_copy','bl_vic_repeat','bl_vic_equal63']:
            # Function size comes from the current unchanged object section.
            obj='sprite_copy' if name=='bl_sprite_copy' else 'vic_compare'
            ob,oss=sections(ROOT/('amiga/out/'+obj+'.o'));s=dict(oss)['.text.'+name];wanted=ob[s[4]:s[4]+s[5]]
            for code,table,addresses in [(raw,ss,oldsyms),(data,secs,syms)]:
                at=addresses[name];q=next(q for n,q in table if q[1]==1 and q[3]<=at and at+len(wanted)<=q[3]+q[5]);off=q[4]+at-q[3];assert code[off:off+len(wanted)]==wanted,(path,name)
    _,old=sections(ROOT/parentelf);_,new=sections(ROOT/'amiga/out/bruce_amiga.elf')
    delta={k:dict(new)[k][5]-dict(old)[k][5] for k in ['.text','.rodata','.data','.bss']}
    assert 0<delta['.text']<=320 and all(delta[k]==0 for k in ['.rodata','.data','.bss'])
    elf=item('amiga/out/bruce_amiga.elf')['sha256']
    for label in ['contact-unroll-r12','contact-unroll-r12-death']:
        p='reference/analysis/render-coherence-2026-10-29/'+label+'/report.json';q=read(p)
        assert q['elf']['sha256']==elf and q['snapshots_paused'] and len(q['samples'])>=12
        for k in ['mixed_phase_samples','max_pixel_mismatch','max_static_pixel_mismatch','max_flicker_illegal_pixels']:assert q[k]==0,k
        assert not q['flicker_stuck_codes'];paths.append(p)
        paths += [f.relative_to(ROOT).as_posix() for f in (ROOT/Path(p).parent).glob('*') if f.suffix in ['.bpl','.bin']]
    boot=read(BASE+'/normal-boot.json');assert boot['cli_complete_menu'] and boot['adf_complete_menu'] and boot['adf_source_progress'] and boot['elf_sha256']==elf
    for e in boot['artifacts']:assert item(e['path'])['sha256']==e['sha256'];paths.append(e['path'])
    paths.append(BASE+'/normal-boot.json')
    outputs=['amiga/out/bruce_amiga.'+s for s in ['exe','elf','adf']]+['.tmp/amiga-boot/c/start']
    assert item(outputs[-1])['sha256']==item(outputs[0])['sha256']
    return dict(parent,date='2026-10-31',status='scoped_complete_contact_alignment_unroll_acceptance_open',largest_chip_block=int(r['chip_largest_loaded']),normal_build=[item(p) for p in outputs],
      contact_unroll=dict(selected=selected,baseline=before,normal_section_deltas=delta,source_rule_changed=False,game_main_unchanged=True,fresh_native_controls=53,fresh_native_loops=1200,prior_original_byte_controls_reused_through_unchanged_core=True),artifacts=[item(p) for p in sorted(set(paths))])
if __name__=='__main__':verify_current();print('PASS bounded contact alignment delivery; overall acceptance remains open')
