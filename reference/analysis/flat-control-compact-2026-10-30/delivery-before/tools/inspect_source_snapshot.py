"""Read-only source-RAM extraction from supported WinUAE USS RAM chunks."""
import argparse,hashlib,json,struct,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('snapshot',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.snapshot.read_bytes();digest=hashlib.sha256(raw).hexdigest();assert raw[:4]==b'ASF '
    chunks={};at=0
    while at+12<=len(raw):
        tag=raw[at:at+4];size,flags=struct.unpack_from('>II',raw,at+4)
        if tag==b'END ':break
        assert size>=12 and at+size<=len(raw)
        data=raw[at+12:at+size]
        if tag in (b'CRAM',b'BRAM'):
            if flags&1:
                length=struct.unpack_from('>I',data)[0];stream=zlib.decompressobj()
                data=stream.decompress(data[4:])+stream.flush();assert stream.eof and not stream.unused_data and len(data)==length
            assert len(data)==524288;chunks[tag]=data
        at+=size+4-size%4
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();found=[]
    for tag,data in chunks.items():
        pos=0
        while True:
            k=data.find(source[0x1167:0x1187],pos)
            if k<0:break
            pos=k+1;base=k-0x1167
            if 0<=base<=len(data)-65536:
                m=data[base:base+65536]
                if m[0x29]<20 and m[0xf2] in (0x38,0x3a,0x3c,0x3e):found.append((tag,base,m))
    assert len(found)==1
    tag,base,m=found[0];a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-memory.bin').write_bytes(m)
    fields={'active':0x95,'input':0x98,'fire':0x9b,'x':0x9e,'y':0xa1,'facing':0xa4,'body_contact':0xa7,'net_hold':0xaa,'net_delay':0xad,'fall_push':0xb0,'contact':0xb6,'state':0xbf,'previous':0xc2,'animation':0xcb,'counter':0xce,'health':0xd1,'wait':0x106,'pose':0x4f48,'mask':0x4f4e}
    r=dict(snapshot_sha256=digest,snapshot_unchanged=hashlib.sha256(a.snapshot.read_bytes()).hexdigest()==digest,
        source_sha256=hashlib.sha256(source).hexdigest(),chunk=tag.decode(),source_base=hex(base),room=m[0x29]+1,
        human_yamo=m[0x42ca],players=m[0x42c9]+1,actors=[dict(actor=i,**{k:m[v+i] for k,v in fields.items()}) for i in range(3)],
        timers={hex(x):m[x] for x in [0x48,0x50,0x5d,0x5e,0x87,0x88,0xd015,0xd01e]},
        edition_verified=False,natural_playthrough=False,method='Stored Amiga source-RAM state; no resume or failed-input inference')
    (a.out/'snapshot.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
