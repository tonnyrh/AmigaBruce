"""Build a private, reproducible sprite-copy experiment; production untouched."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/sprite-disjoint-2026-10-30'

FAST_C=r'''
static unsigned char source_sprite_disjoint_c(void){
    unsigned short dest=W(0x0e),first=W(0x26ab),left=W(0x26e4),right=W(0x26ee),i;
    unsigned char h=m[0xe0+x],wide=(unsigned char)!z;
    if((dest&1) || dest<0x8000 || dest>0xff00 || (dest>=0xcf00 && dest<0xe000) ||
       first<0x3000 || first>0x7f00 || left<0x3000 || left>0x7f00 || right<0x3000 || right>0x7f00 ||
       y!=3*h || (!wide && h>20) || (wide && (!h || h>21)))return 0;
    for(i=0;i<64;i++)m[dest+i]=0;
    if(wide){for(i=0;i<h;i++){m[dest+3*i]=m[right+2*i];m[dest+3*i+1]=m[left+2*i+1];}c=0;}
    else for(i=0;i<=h;i++)m[dest+3*i]=m[first+i];
    m[0x277f]=255;x=255;y=64;a=0;z=0;n=1;sp+=2;return 1;
}
'''

ASM=r'''
    /* The conservative source window excludes code operands, count scratch,
     * destination, wraparound and mapped I/O. All other cases keep ordering. */
    move.w 0(%a4),%d0
    btst #0,%d0
    bne .Lsprite_ordered
    cmpi.w #0xcf00,%d0
    blo.s .Lfast_dest_ok
    cmpi.w #0xe000,%d0
    blo .Lsprite_ordered
.Lfast_dest_ok:
    move.w 2(%a4),%d0
    cmpi.w #0x3000,%d0
    blo .Lsprite_ordered
    cmpi.w #0x7f00,%d0
    bhi .Lsprite_ordered
    move.w 4(%a4),%d0
    cmpi.w #0x3000,%d0
    blo .Lsprite_ordered
    cmpi.w #0x7f00,%d0
    bhi .Lsprite_ordered
    move.w 6(%a4),%d0
    cmpi.w #0x3000,%d0
    blo .Lsprite_ordered
    cmpi.w #0x7f00,%d0
    bhi .Lsprite_ordered
    move.w %d2,%d0
    add.w %d0,%d0
    add.w %d2,%d0
    cmp.w %d3,%d0
    bne .Lsprite_ordered
    tst.b 10(%a4)
    bne.s .Lfast_wide_guard
    cmpi.w #20,%d2
    bhi .Lsprite_ordered
    bra.s .Lfast_clear
.Lfast_wide_guard:
    tst.w %d2
    beq .Lsprite_ordered
    cmpi.w #21,%d2
    bhi .Lsprite_ordered
.Lfast_clear:
    move.l %a0,%a5
    .rept 16
    clr.l (%a5)+
    .endr
    tst.b 10(%a4)
    bne.s .Lfast_wide
.Lfast_narrow_loop:
    move.b (%a1)+,(%a0)
    addq.l #3,%a0
    dbra %d2,.Lfast_narrow_loop
    bra.s .Lfast_done
.Lfast_wide:
    clr.b 11(%a4)
    addq.l #1,%a2
    subq.w #1,%d2
.Lfast_wide_loop:
    move.b (%a3),(%a0)+
    move.b (%a2),(%a0)
    addq.l #2,%a0
    addq.l #2,%a2
    addq.l #2,%a3
    dbra %d2,.Lfast_wide_loop
.Lfast_done:
    move.b #-1,0x277f(%a6)
    move.b #-1,8(%a4)
    move.b #64,9(%a4)
    movem.l (%sp)+,%d2-%d5/%a2-%a6
    rts
.Lsprite_ordered:
'''

def main():
    BASE.mkdir(parents=True,exist_ok=True)
    for sub in ['before','candidate']:(BASE/sub).mkdir(exist_ok=True)
    for name in ['c64_rooms.c','c64_actor_programs.h']:
        raw=(ROOT/'core'/name).read_bytes()
        for sub in ['before','candidate']:(BASE/sub/name).write_bytes(raw)
    asm=(ROOT/'amiga/sprite_copy.s').read_text()
    (BASE/'before/sprite_copy.s').write_text(asm)
    anchor='    moveq #63,%d4\n'
    assert asm.count(anchor)==1
    (BASE/'candidate/sprite_copy.s').write_text(asm.replace(anchor,ASM+anchor))
    # Host proof uses the exact same guarded transform, plus original fallback.
    core=(BASE/'candidate/c64_rooms.c').read_text(encoding='utf-8-sig')
    anchor='static unsigned char source_sprite_copy(void){'
    core=core.replace(anchor,FAST_C+'\n'+anchor)
    core=core.replace('    source_sprite_copy_c();return 1;','    if(!source_sprite_disjoint_c())source_sprite_copy_c();return 1;')
    # Retain all192 alias/tail cases; first64 now exercise the guarded native
    # path at every height0..31 in both widths, including rejected heights.
    core=core.replace('glyph=test<64?0xa200:', 'glyph=test<64?0x5d91:')
    core=core.replace('y=z?ys[(test>>3)&7]:(unsigned char)(height*3);',
        'y=(test<64 || !z)?(unsigned char)(height*3):ys[(test>>3)&7];')
    (BASE/'candidate/c64_rooms.c').write_text(core,encoding='utf-8')
    bridge=(ROOT/'tests/source_contact_bridge.c').read_text()
    bridge=bridge.replace('#include "../core/c64_rooms.c"','#include "candidate/c64_rooms.c"')
    (BASE/'bridge.c').write_text(bridge)
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    paths=[ROOT/p for p in ['core/c64_rooms.c','core/c64_actor_programs.h','amiga/sprite_copy.s']]
    paths+=[BASE/p for p in ['before/c64_rooms.c','before/c64_actor_programs.h','before/sprite_copy.s','candidate/c64_rooms.c','candidate/c64_actor_programs.h','candidate/sprite_copy.s','bridge.c']]
    (BASE/'scope.json').write_text(json.dumps(dict(status='isolated_disjoint_sprite_candidate',production_changed=False,source_sha256=hashlib.sha256((ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()).hexdigest(),artifacts=[item(p) for p in paths]),indent=2)+'\n')
    print('Private sprite-copy candidate generated; production unchanged')
if __name__=='__main__':main()
