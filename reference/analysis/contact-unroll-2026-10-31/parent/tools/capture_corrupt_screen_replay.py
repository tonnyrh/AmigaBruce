"""Owned replay of a copy of the user's USS; exact paused RAM/frame captures."""
import argparse,hashlib,json,re,time
from pathlib import Path
from winuae_ipc import command
from capture_paula_stream import elf_symbols
from audit_vic_native_kernels import sections
from preview_planar import render
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reference/analysis/screen-corruption-2026-10-30'
def main():
    p=argparse.ArgumentParser();p.add_argument('--pid',required=True,type=int);p.add_argument('--label',required=True);p.add_argument('--samples',type=int,default=3);a=p.parse_args()
    runtime=ROOT/'.tmp/corrupt-screen-ui';pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",(runtime/'winuaebootlog.txt').read_text(errors='replace'))[-1]
    def cmd(s):return command(pipe,s,expected_pid=a.pid)
    def read(at,n):
        if n>128:
            temp=runtime/('read-%x-%x.bin'%(at,n))
            assert 'Wrote ' in cmd('DBG S %s %x %x'%(temp,at,n))
            result=temp.read_bytes();assert len(result)==n;return result
        out=bytearray()
        for off in range(0,n,256):
            reply=cmd('DBG m %x %x'%(at+off,min(16,(n-off+15)//16)))
            for line in reply.splitlines():
                m=re.match(r'^[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{4}\s+){1,8})',line)
                if m:out.extend(bytes.fromhex(m[1]))
        assert len(out)>=n,(hex(at),n,len(out));return bytes(out[:n])
    def long(at):return int.from_bytes(read(at,4),'big')
    elf=ROOT/'reference/analysis/audio-service-2026-10-30/parent/amiga/out/bruce_amiga.elf'
    _,ss=sections(elf);_,symbols=elf_symbols(elf);labels=['.text','.rodata','.data','.bss'];s=[next(q for k,q in ss if k==name) for name in labels]
    task=long(long(4)+276);node=long(long(task+172)*4+60)*4;hunks=[]
    while node:hunks.append(node+4);node=long(node)*4;assert len(hunks)<=8
    def addr(name):
        v=symbols[name];i=next(i for i,q in enumerate(s) if q[3]<=v<q[3]+q[5]);return hunks[i]+v-s[i][3]
    def pause():cmd('EVT SPC_PAUSE 1');cmd('EVT SPC_PAUSE 0');time.sleep(.1)
    out=BASE/a.label;out.mkdir(exist_ok=True);rows=[]
    for i in range(a.samples):
        pause()
        try:
            m=read(addr('m'),65536);(out/('sample%d-source.bin'%i)).write_bytes(m)
            row=dict(room=m[0x29]+1,actors=list(m[0x95:0x98]),hunks=[hex(v) for v in hunks],cpu=cmd('DBG r'))
            for name,n in [('loaded',1),('paint_bank',1),('actor_loading_pending',1),('game_field_loading',1),('actor_logic_steps',2),('actor_loading_epoch',2),('source_fault',2),('paint_count',2),('paint_cursor',2),('contact_generation',2),('index_ready',1)]:row[name]=int.from_bytes(read(addr(name),n),'big')
            for name,n in [('indexed_screen',1000),('cell_cache',2000),('character_cache',40960)]:
                (out/('sample%d-%s.bin'%(i,name))).write_bytes(read(addr(name),n))
            for name in ['background','buffers']:
                for j in range(2 if name=='buffers' else 1):
                    ptr=long(addr(name)+4*j);bp=out/('sample%d-%s%d.bpl'%(i,name,j));bp.write_bytes(read(ptr,40960));render(bp,bp.with_suffix('.png'),interleaved=True)
                    row[name+str(j)]=hex(ptr)
            rows.append(row);print('Captured',i,row['room'],row['actor_loading_pending'],row['source_fault'],flush=True)
        finally:pause()
        time.sleep(2)
    (out/'report.json').write_text(json.dumps(dict(method='Resume private USS copy in owned PAL A500 process; captures paused. No source RAM injection.',pid=a.pid,elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),samples=rows),indent=2)+'\n')
if __name__=='__main__':main()
