"""Strict comparison permitting only ELF-declared .data alignment padding.

elf2hunk copies up to three bytes beyond the initialized .data section.
Those bytes can vary between conversions. Code, initialized data, BSS sizes,
all relocations, symbols and the rest of the file must remain identical.
"""
from pathlib import Path
import hashlib,struct
def artifact(p,root):return dict(path=p.relative_to(root).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def compare(current,tested,elf,root):
    e=elf.read_bytes();assert e[:6]==b'\x7fELF\x01\x02'
    off=struct.unpack_from('>I',e,32)[0];size,count,idx=struct.unpack_from('>HHH',e,46)
    sections=[struct.unpack_from('>10I',e,off+i*size) for i in range(count)]
    tab=sections[idx];names=e[tab[4]:tab[4]+tab[5]]
    data=[s for s in sections if names[s[0]:names.index(0,s[0])]==b'.data'][0]
    a=current.read_bytes();b=tested.read_bytes();assert len(a)==len(b)
    at=0
    def u():
        nonlocal at
        value=struct.unpack_from('>I',a,at)[0];at+=4;return value
    assert u()==0x3f3 and u()==0
    count=u();first=u();last=u();assert (count,first,last)==(4,0,3)
    sizes=[u() for _ in range(4)];hunk=0;allowed=set();ends=0
    while at<len(a):
        t=u();assert t in (0x3e9,0x3ea,0x3eb,0x3ec,0x3f0,0x3f1,0x3f2)
        if t in (0x3e9,0x3ea,0x3f1):
            n=u()
            if t==0x3ea and hunk==2:
                assert 0<=n*4-data[5]<=3
                assert a[at:at+data[5]]==e[data[4]:data[4]+data[5]]
                allowed.update(range(at+data[5],at+n*4))
            at+=n*4
        elif t==0x3eb:u()
        elif t==0x3ec:
            while True:
                n=u()
                if not n:break
                u();at+=n*4
        elif t==0x3f0:
            while True:
                n=u()
                if not n:break
                at+=n*4+4
        elif t==0x3f2:hunk+=1;ends+=1
    assert at==len(a) and ends==4 and allowed
    differences=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    assert set(differences)<=allowed,('Executable changed outside unused .data padding',differences[:10],sorted(allowed))
    return dict(status='all_program_bytes_identical_except_unused_data_alignment_padding',
        current=artifact(current,root),tested=artifact(tested,root),current_elf=artifact(elf,root),
        initialized_data_bytes=data[5],allocation_data_bytes=sizes[2]*4,
        allowed_offsets=sorted(allowed),different_offsets=differences,
        code_initialized_data_bss_relocations_symbols_identical=True)
