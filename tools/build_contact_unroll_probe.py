"""Private fixed-count 68000 contact-alignment experiment; no game changes."""
import hashlib,json
from pathlib import Path
from build_stationary_enemy_probe import HELPER
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/contact-unroll-2026-10-31'

def candidate(text,byte_loops=False,shift_loops=True):
    pairs=[('    moveq #7,%d0\n3:\n    clr.l (%a1)+\n    dbra %d0,3b',
            '    .rept 8\n    clr.l (%a1)+\n    .endr'),
           ('    moveq #23,%d0\n6:\n    move.l (%a2)+,(%a1)+\n    dbra %d0,6b',
            '    .rept 24\n    move.l (%a2)+,(%a1)+\n    .endr')]
    for label in (['10','15'] if shift_loops else []):
        start=text.index(label+':\n')+len(label)+2
        tail=f'    subq.l #4,%a3\n    cmpa.l %a0,%a3\n    bcc.s {label}b'
        stop=text.index(tail,start)
        body=text[start:stop]
        pairs.append((label+':\n'+body+tail,
                      '    .rept 8\n'+body+'    subq.l #4,%a3\n    .endr'))
    for old,new in pairs:
        assert text.count(old)==1
        text=text.replace(old,new)
    if byte_loops:
        for old,new in [
          ('    moveq #31,%d0\n21:\n    clr.b (%a1)+\n    dbra %d0,21b','    .rept 32\n    clr.b (%a1)+\n    .endr'),
          ('    moveq #95,%d0\n8:\n    move.b (%a2)+,(%a1)+\n    dbra %d0,8b','    .rept 96\n    move.b (%a2)+,(%a1)+\n    .endr')]:
            assert text.count(old)==1
            text=text.replace(old,new)
        text=text.replace('    bra.s 9f','    bra 9f')
    # Expansion places these branches outside the old short displacement.
    text=text.replace('    bne.s 7f','    bne 7f').replace('    bcs.s 7f','    bcs 7f')
    text=text.replace('    beq.s 10f','    beq 10f')
    # The phase-one/two target still needs its entry label.
    if shift_loops:
        anchor='    .rept 8\n    move.l (%a3),%d2'
        assert text.count(anchor)==2
        text=text.replace(anchor,'10:\n'+anchor,1)
    return text

def main():
    BASE.mkdir(exist_ok=True)
    main=(ROOT/'amiga/main.c').read_text(encoding='utf-8-sig')
    allocation='if(BL_AUTOTEST){capture=AllocMem(BL_CAPTURE_BYTES,MEMF_PUBLIC|MEMF_CLEAR);tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}'
    guard='(BL_AUTOTEST&&(!capture||!tone))'
    assert main.count(allocation)==main.count(guard)==1
    main=main.replace(allocation,'if(BL_AUTOTEST){tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}').replace(guard,'(BL_AUTOTEST&&!tone)')
    anchor='int main(void) {';assert main.count(anchor)==1
    main=main.replace(anchor,'extern void bl_enemy_stationary_probe(unsigned long *out);\nextern unsigned long bl_enemy_probe_ram(void);\nstatic ULONG enemy_stationary[40],enemy_stationary_mem;\n'+anchor)
    anchor='    intro_start=field_clock();';assert main.count(anchor)==1
    main=main.replace(anchor,'    bl_enemy_stationary_probe(enemy_stationary);enemy_stationary_mem=TypeOfMem((APTR)bl_enemy_probe_ram());\n'+anchor)
    anchor='        append(&p,"\\nsource_clock_elapsed=");number(&p,source_clock_elapsed);'
    assert main.count(anchor)==1
    block='''        append(&p,"\\nenemy_stationary_ram_type=");number(&p,enemy_stationary_mem);
        {UWORD q,j;for(q=0;q<8;q++){append(&p,"\\nenemy_stationary_");number(&p,q);append(&p,"=");
        for(j=0;j<5;j++){if(j)append(&p,",");number(&p,enemy_stationary[q*5+j]);}}}
'''
    main=main.replace(anchor,block+anchor)
    align=(ROOT/'amiga/contact_align.s').read_text()
    variants=['baseline','candidate','candidate-byte','candidate-compact']
    for variant in variants:
        folder=BASE/variant;folder.mkdir(exist_ok=True)
        (folder/'main.c').write_text(main,encoding='utf-8')
        (folder/'c64_rooms.c').write_text((ROOT/'core/c64_rooms.c').read_text(encoding='utf-8-sig')+HELPER,encoding='utf-8')
        (folder/'c64_actor_programs.h').write_bytes((ROOT/'core/c64_actor_programs.h').read_bytes())
        (folder/'contact_align.s').write_text(align if variant=='baseline' else candidate(align,variant in ['candidate-byte','candidate-compact'],variant!='candidate-compact'),encoding='utf-8')
        builder=(ROOT/'amiga-build.ps1').read_text(encoding='utf-8-sig')
        builder=builder.replace('$taskRoot=$PSScriptRoot',f"$taskRoot='{ROOT}'",1)
        anchor='    & $compiler @sourceFlags -c (Join-Path $taskRoot $source) -o $obj'
        assert builder.count(anchor)==1
        replacements=['    $actualPath=Join-Path $taskRoot $source']
        for source in ['amiga/main.c','core/c64_rooms.c','amiga/contact_align.s']:
            rel=(folder/Path(source).name).relative_to(ROOT).as_posix()
            replacements.append(f"    if($source -eq '{source}'){{$actualPath=Join-Path $taskRoot '{rel}';$sourceFlags+='-I'+(Join-Path $taskRoot '{Path(source).parent.as_posix()}')}}")
        replacements.append('    & $compiler @sourceFlags -c $actualPath -o $obj')
        builder=builder.replace(anchor,'\n'.join(replacements))
        if variant!='baseline':
            builder=builder.replace("'amiga/out'",f"'reference/analysis/contact-unroll-2026-10-31/{variant}/out'")
        (BASE/(variant+'-build.ps1')).write_text(builder,encoding='utf-8')
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    paths=[ROOT/p for p in ['amiga/main.c','core/c64_rooms.c','core/c64_actor_programs.h','amiga/contact_align.s','amiga/out/bruce_amiga.exe','amiga/out/bruce_amiga.elf']]
    generated=[BASE/(v+'-build.ps1') for v in variants]+[BASE/v/p for v in variants for p in ['main.c','c64_rooms.c','c64_actor_programs.h','contact_align.s']]
    (BASE/'scope.json').write_text(json.dumps(dict(production_changed=False,inputs=[item(p) for p in paths],generated=[item(p) for p in generated],method='Same ordered byte/long accesses and same guards; unroll only fixed-length loops. Identical current-main stationary + PAL harness for all variants. No extra service seam.'),indent=2)+'\n')
    print('Built private baseline/candidate contact alignment inputs')
if __name__=='__main__':main()
