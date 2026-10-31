"""Verify the bounded Copper commit and bind the native rendering checks.

This is Amiga publication evidence, not original C64 raster certification.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
from verify_renderer_delta_scope import verify as renderer_scope,effective_source_path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/publication-2026-10-30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def verify():
    derivation=renderer_scope()
    before=BASE/'before'
    for item in load(before/'manifest.json'):
        assert sha(before/item['path'])==item['sha256']
    frozen=load(ROOT/'reference/analysis/final-colors-2026-10-30/final-file-freeze.json')
    # Source identity is checked below against the immediately preceding stage.
    entries=frozen if isinstance(frozen,list) else frozen.get('files',[])
    for item in entries:
        if item['path'].startswith('core/'):
            assert sha(effective_source_path(item['path']))==item['sha256'],item['path']
    extension=sorted((Path.home()/'.vscode/extensions').glob('bartmanabyss.amiga-debug-*'))[-1]
    dump=extension/'bin/win32/opt/bin/m68k-amiga-elf-objdump.exe'
    elf=ROOT/'amiga/out/bruce_amiga.elf'
    asm=subprocess.check_output([str(dump),'-d','--disassemble=present_frame.isra.0',str(elf)],text=True)
    assert '<present_frame.isra.0>' in asm
    assert 'addi.w #-300,d0' in asm and 'cmpi.w #8,d0' in asm
    branch=asm.index('bhi.s');commit=asm.index('dff080')
    assert branch<commit and not re.search(r'\bjsr\b',asm[branch:commit])
    accepted=[line for line in range(512) if ((line-300)&65535)<=8]
    assert accepted==list(range(300,309))
    (BASE/'normal-commit-disassembly.txt').write_text(asm,encoding='utf-8')
    report=dict(status='passed_scoped_publication_guard',source_gameplay_unchanged=True,
        accepted_raster_lines=accepted,edition_verified=False,natural_playthrough=False,
        realtime_accepted=False,normal_exe_sha256=sha(ROOT/'amiga/out/bruce_amiga.exe'),
        normal_elf_sha256=sha(elf),main_sha256=sha(ROOT/'amiga/main.c'),renderer_derivation=derivation,
        native_tour=None,render_samples=[])
    tour=ROOT/'reference/analysis/optimization-2026-10-27/publication-guard-tour/identity.json'
    assert tour.exists(), 'Native 20-room evidence required'
    if tour.exists():
        r=load(tour);run=r['run']
        assert len(r['rooms'])==20 and int(run['bad_presents'])==0
        assert int(run['contact_kernel_cases'])==710 and int(run['sprite_copy_cases'])==256
        assert all(room['steps']==120 and room['chip_largest']>=49152 for room in r['rooms'])
        for key in ['source_tour_error','c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','vic_compare_errors','contact_kernel_errors']:
            assert int(run[key])==0,key
        for item in r['build']:
            assert sha(tour.parent/item['path'])==item['sha256']
        assert 300<=int(run['present_min_line'])<=int(run['present_max_line'])<=308
        report['native_tour']=dict(path=tour.relative_to(ROOT).as_posix(),sha256=sha(tour),
            rooms=20,present_min_line=run['present_min_line'],present_max_line=run['present_max_line'],
            bad_fields=run['bad_presents'],room12=r['rooms'][11])
    for label in ['incident-current-r12','observer-native','observer-native-death']:
        p=ROOT/'reference/analysis/render-coherence-2026-10-29'/label/'report.json'
        assert p.exists(),label
        if p.exists():
            r=load(p)
            assert len(r['samples'])>=(12 if label!='incident-current-r12' else 6) and r['snapshots_paused']
            assert r['mixed_phase_samples']==r['max_static_pixel_mismatch']==0
            if label!='incident-current-r12':
                assert r['elf']['sha256']==sha(elf) and r['max_flicker_illegal_pixels']==0
            report['render_samples'].append(dict(label=label,samples=len(r['samples']),sha256=sha(p),
                mixed_phase_samples=0,static_errors=0,controlled_death=r['controlled_death'],roundtrip=r['room_roundtrip']))
    assert report['render_samples'][-1]['controlled_death'] and report['render_samples'][-1]['roundtrip']
    assert sha(ROOT/'.tmp/amiga-boot/c/start')==report['normal_exe_sha256']
    report['paint_controls']=load(ROOT/'reference/validation/source-paint-host.json')['cases']
    report['source_freeze_sha256']=sha(ROOT/'reference/analysis/final-colors-2026-10-30/final-file-freeze.json')
    (BASE/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':verify()

