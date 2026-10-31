"""Execute actual frozen6502 bytes against the isolated disjoint transform."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/sprite-disjoint-2026-10-30'

def main():
    text=(ROOT/'tools/verify_source_sprite_copy.py').read_text()
    text=text.replace("ROOT=Path(__file__).resolve().parents[1]",'ROOT=Path('+repr(str(ROOT))+')')
    text=text.replace(".tmp/source-contact-test/contact.dll",'.tmp/sprite-disjoint-host/candidate.dll')
    anchor='    for index,(wide,height,yy,(dest,glyph),flags) in enumerate(cases):'
    extra='''    cases += [(w,h,3*h,(dest,glyph),flags)
        for w in [0,1] for h in [0,1,11,20,21,22,31]
        for dest,glyph in [(0xa000,0x5d91),(0xa002,0x3000),(0xa000,0x7f00),
            (0xa000,0x2fff),(0xa000,0x7f01),(0xcf00,0x5d91),
            (0xd000,0x5d91),(0xe000,0x5d91),(0xff00,0x5d91),
            (0xa001,0x5d91),(0xa000,0xa000),(0xa000,0x2770)] for flags in [0,0xc9]]
    selected=sum(1 for w,h,yy,(dest,glyph),flags in cases
        if not flags&8 and dest%2==0 and 0x8000<=dest<=0xff00 and not 0xcf00<=dest<0xe000
        and 0x3000<=glyph<=0x7eff and yy==3*h and (1<=h<=21 if w else h<=20))
    assert selected==32
'''
    assert text.count(anchor)==1
    text=text.replace(anchor,extra+anchor)
    text=text.replace("paths=['core/c64_rooms.c'", "paths=['reference/analysis/sprite-disjoint-2026-10-30/candidate/c64_rooms.c'")
    text=text.replace("report=dict(status='passed_original_sprite_copy_bytes',", "report=dict(selected_fast_cases=selected,status='passed_disjoint_sprite_copy_source_bytes',")
    text=text.replace('reference/validation/source-sprite-copy-host.json','reference/analysis/sprite-disjoint-2026-10-30/source-proof.json')
    # Persist the exact executed test (including unchanged RAM/register oracle).
    (BASE/'executed-source-proof.py').write_text(text)
    exec(compile(text,str(BASE/'executed-source-proof.py'),'exec'),{'__name__':'__main__','__file__':str(Path(__file__))})
if __name__=='__main__':main()
