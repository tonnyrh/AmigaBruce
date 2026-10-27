"""Read-only inspection of this user's WinUAE USS; never resumes or rewrites it.

Decodes only the supported ASF/CRAM/BRAM layout, validates every length and
zlib stream, and locates source RAM by frozen table bytes plus live fields.
The frame is reconstructed from a matching stored Copper list, not an
emulator screenshot or a C64 gameplay observation.
"""
from pathlib import Path
import hashlib
import json
import struct
import zlib
from preview_planar import render

ROOT=Path(__file__).resolve().parents[1]


def inspect(path):
    data=path.read_bytes();before=hashlib.sha256(data).hexdigest()
    assert data[:4]==b'ASF '
    chunks={};at=0;inventory=[]
    while at+8<=len(data):
        tag=data[at:at+4].decode('ascii');size=struct.unpack_from('>I',data,at+4)[0]
        if tag=='END ':assert size==8;break
        assert size>=12 and at+size<=len(data)
        flags=struct.unpack_from('>I',data,at+8)[0]
        payload=data[at+12:at+size];raw=payload
        if tag in ('CRAM','BRAM'):
            assert flags in (0,1)
            if flags:
                expected=struct.unpack_from('>I',payload)[0]
                stream=zlib.decompressobj();raw=stream.decompress(payload[4:])+stream.flush()
                assert stream.eof and not stream.unused_data and len(raw)==expected
            assert len(raw)==524288
        chunks[tag]=raw;inventory.append(dict(tag=tag,offset=at,size=size,flags=flags))
        at+=size+4-size%4
    assert 'CRAM' in chunks and 'BRAM' in chunks
    frozen=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    slow=chunks['BRAM'];start=0;candidates=[]
    while True:
        found=slow.find(frozen[0x1167:0x1187],start)
        if found<0:break
        base=found-0x1167;start=found+1
        if 0<=base<=len(slow)-65536:
            m=slow[base:base+65536]
            if m[0x29]<20 and 12<=m[0x9e]<=163 and 45<=m[0xa1]<=199 and m[0xf2] in (0x38,0x3a,0x3c,0x3e):
                candidates.append((base,m))
    assert len(candidates)==1,len(candidates)
    base,m=candidates[0]
    scratch=ROOT/'.tmp/climb-snapshot';scratch.mkdir(parents=True,exist_ok=True)
    for name in ('CRAM','BRAM'):(scratch/(name+'.bin')).write_bytes(chunks[name])
    (scratch/'source-memory.bin').write_bytes(m)
    chip=chunks['CRAM'];signature=bytes.fromhex('0180000001820fff01840833018607cc')
    copper=chip.find(signature);assert copper>=32
    ptrs=[]
    for plane in range(4):
        reg,hi,reg2,lo=struct.unpack_from('>HHHH',chip,copper-32+plane*8)
        assert (reg,reg2)==(0xe0+plane*4,0xe2+plane*4)
        ptrs.append(hi*65536+lo)
    assert ptrs==[ptrs[0]+40*p for p in range(4)]
    frame=scratch/'frame.bpl';frame.write_bytes(chip[ptrs[0]:ptrs[0]+40960]);assert frame.stat().st_size==40960
    image=ROOT/'docs/images/climb-snapshot-r05.png';render(frame,image,interleaved=True)
    result=dict(snapshot=dict(path=path.relative_to(ROOT).as_posix(),sha256=before,size_bytes=len(data)),
        snapshot_unchanged=hashlib.sha256(path.read_bytes()).hexdigest()==before,
        source_sha256=hashlib.sha256(frozen).hexdigest(),edition_verified=False,
        source_ram_address=f'${0xc00000+base:06X}',room=m[0x29]+1,
        source_room_tick_anchor=[m[0x9e]*2-24,m[0xa1]],
        frame=dict(path=image.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                   method='Reconstructed stored planar bitmap from matching Copper list',bitplanes=ptrs),
        chunks=inventory,
        limits=['Amiga snapshot contains the prior custom-art build',
                'Source room tick coordinates do not identify every live BlGame field or failed input',
                'Sequential comparison recreates controlled room5 states; it does not resume this USS'])
    out=ROOT/'reference/analysis/climb-audit-2026-10-25/snapshot.json'
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    print(json.dumps(inspect(ROOT/'.tmp/25.10.2026.uss'),indent=2))
