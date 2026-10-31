"""Read-only USS inspection; do not resume or modify the user's snapshot."""
import argparse,hashlib,json,struct,zlib
from pathlib import Path
from audit_vic_native_kernels import sections
from capture_paula_stream import elf_symbols
from preview_planar import render
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reference/analysis/screen-corruption-2026-10-30'
def chunks(path):
    raw=path.read_bytes();assert raw[:4]==b'ASF ';at=0;result={}
    while at+12<=len(raw):
        tag=raw[at:at+4].decode();size,flags=struct.unpack_from('>II',raw,at+4)
        if tag=='END ':break
        assert size>=12 and at+size<=len(raw)
        blob=raw[at+12:at+size]
        if flags&1 and tag in ['CRAM','BRAM']:
            length=struct.unpack_from('>I',blob)[0];stream=zlib.decompressobj();blob=stream.decompress(blob[4:])+stream.flush()
            assert stream.eof and not stream.unused_data and len(blob)==length
        result[tag]=blob;at+=size+4-size%4
    return result
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--elf',type=Path,default=ROOT/'amiga/out/bruce_amiga.elf');args=parser.parse_args()
    path=ROOT/'.tmp/30.10.2026.uss';sha=hashlib.sha256(path.read_bytes()).hexdigest();c=chunks(path);OUT.mkdir(exist_ok=True)
    def read(addr,n):
        if 0<=addr and addr+n<=len(c['CRAM']):return c['CRAM'][addr:addr+n]
        if 0xc00000<=addr and addr+n<=0xc00000+len(c['BRAM']):return c['BRAM'][addr-0xc00000:addr-0xc00000+n]
        raise AssertionError(('Unsupported address',hex(addr),n))
    def long(addr):return int.from_bytes(read(addr,4),'big')
    task=long(long(4)+276);cli=long(task+172)*4;node=long(cli+60)*4;hunks=[]
    while node:hunks.append(node+4);node=long(node)*4;assert len(hunks)<=8
    elf=args.elf.resolve();e,ss=sections(elf);bss,syms=elf_symbols(elf)
    labels=['.text','.rodata','.data','.bss'];mapping={name:next(s for label,s in ss if label==name) for name in labels}
    def addr(name):
        value=syms[name];i=next(i for i,k in enumerate(labels) if mapping[k][3]<=value<mapping[k][3]+mapping[k][5]);return hunks[i]+value-mapping[labels[i]][3]
    m=read(addr('m'),65536);assert m==(OUT/'source-memory.bin').read_bytes()
    # Decode ELF relocation records and apply runtime hunk placement.
    text=mapping['.text'];wanted=bytearray(e[text[4]:text[4]+text[5]])
    symtab=next(s for _,s in ss if s[1]==2);relocs=[]
    for name,s in ss:
        if s[1] not in (4,9) or s[7]!=ss.index(('.text',text)):continue
        for at in range(s[4],s[4]+s[5],s[9]):
            offset,info=struct.unpack_from('>II',e,at);kind=info&255;index=info>>8
            _,value,_,_,_,idx=struct.unpack_from('>IIIBBH',e,symtab[4]+index*symtab[9])
            if kind!=1:continue
            sec=ss[idx][1];target=next((i for i,k in enumerate(labels) if mapping[k]==sec),None)
            if target is None:continue
            p=offset-text[3];old=int.from_bytes(wanted[p:p+4],'big');delta=hunks[target]-sec[3]
            wanted[p:p+4]=((old+delta)&0xffffffff).to_bytes(4,'big');relocs.append(p)
    actual=read(hunks[0],len(wanted));diff=[i for i,(a,b) in enumerate(zip(actual,wanted)) if a!=b]
    globals={}
    for name in ['background','fighter_dma','tile_dma','actor_logic_steps','actor_loading_epoch','source_fault','game_field_last','game_field_loading','game_field_active','actor_loading_pending','actor_delay_pending','actor_gameover_pending','actor_reset_pending','transition_pending','room_reload_required','animation_phase','animation_count']:
        if name in syms:globals[name]=dict(address=hex(addr(name)),bytes=read(addr(name),4).hex())
    frames=[];chip=c['CRAM']
    for p in range(0,len(chip)-64,2):
        regs=struct.unpack_from('>16H',chip,p)
        if regs[::2]!=tuple(v for plane in range(4) for v in (0xe0+plane*4,0xe2+plane*4)):continue
        ptr=[regs[i*4+1]*65536+regs[i*4+3] for i in range(4)]
        if ptr!=[ptr[0]+40*i for i in range(4)] or not 0<=ptr[0]<=len(chip)-40960:continue
        bp=OUT/('copper-%06x.bpl'%p);bp.write_bytes(read(ptr[0],40960));render(bp,bp.with_suffix('.png'),interleaved=True)
        frames.append(dict(copper=hex(p),planes=[hex(v) for v in ptr],bitmap=bp.relative_to(ROOT).as_posix()))
    background=long(addr('background'));bp=OUT/'background.bpl';bp.write_bytes(read(background,40960));render(bp,bp.with_suffix('.png'),interleaved=True)
    for tag in ['CPU ','CPUX','CUST']:
        if tag in c:(OUT/(tag.strip()+'.bin')).write_bytes(c[tag])
    report=dict(snapshot_sha256=sha,snapshot_unchanged=hashlib.sha256(path.read_bytes()).hexdigest()==sha,room=m[0x29]+1,source_display_control=hex(m[0xd011]),source_den=bool(m[0xd011]&16),task=hex(task),hunks=[hex(v) for v in hunks],
       source_ram=hex(addr('m')),elf_path=elf.relative_to(ROOT).as_posix(),elf_sha256=hashlib.sha256(e).hexdigest(),text_bytes=len(wanted),text_relocations=len(relocs),text_matches_selected_elf=not diff,text_diff_offsets=diff[:30],
       globals=globals,frames=frames,chunks={k:len(v) for k,v in c.items()},cpu_head=c.get('CPU ',b'')[:100].hex(),method='Read-only stored RAM/ELF relocation comparison and Copper bitmap reconstruction; no resume or failed-input inference')
    (OUT/'native-snapshot.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
