"""Generate exact aligned OR groups from the frozen contact-class operands."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
MARK='/* GENERATED_CONTACT_CLASSES_BEGIN */'
def generate(source):
    assert hashlib.sha256(source).hexdigest()==SHA
    lines=[MARK,'/* Fixed byte sets from $545C-$558B; no extra byte is read. */',
        '    .section .text.bl_contact_classes4,"ax"','    .globl bl_contact_classes4','bl_contact_classes4:',
        '    move.l 4(%sp),%a0','    moveq #0,%d0']
    for slot,(start,end) in enumerate([(0x545c,0x54ad),(0x54b2,0x5503),(0x5508,0x5547),(0x554c,0x558b)]):
        assert all(source[pc] in (0xad,0x0d) for pc in range(start,end,3))
        remaining={int.from_bytes(source[pc+1:pc+3],'little') for pc in range(start,end,3)}
        original=set(remaining);covered=set();lines += [f'/* ${0x4f3c+slot:04X} */','    moveq #0,%d1']
        while remaining:
            at=min(remaining);size=1
            if not at&1:
                if all(at+i in remaining for i in range(4)):size=4
                elif at+1 in remaining:size=2
            group=set(range(at,at+size));assert not group&covered and group<=remaining
            assert size==1 or not at&1
            remaining-=group;covered|=group
            lines.append(f'    or.{ {1:"b",2:"w",4:"l"}[size]} 0x{at:04x}(%a0),%d1')
        assert covered==original
        lines += ['    tst.l %d1',f'    beq.s {slot+1}f',f'    ori.b #{1<<slot},%d0',f'{slot+1}:']
    lines += ['    rts','']
    return '\n'.join(lines)
def main():
    p=ROOT/'amiga/contact_rows.s';text=p.read_text(encoding='utf-8');prefix=text.split(MARK)[0].rstrip()+'\n'
    p.write_bytes((prefix+generate((ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes())).encode('utf-8'))
    print('Generated aligned class OR groups from frozen source operands')
if __name__=='__main__':main()
