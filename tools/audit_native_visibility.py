"""Controlled source-flag lifecycle in one explicitly owned normal WinUAE.
Injected state, not a natural C64 recording or a resume of the user's USS.
"""
import argparse,hashlib,json,re,struct,subprocess,sys,time
from pathlib import Path
from winuae_ipc import command
from capture_paula_stream import elf_symbols
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--log',type=Path,required=True);a=p.parse_args()
    pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",a.log.read_text(errors='replace'))[-1]
    def cmd(s):return command(pipe,s,expected_pid=a.pid)
    def read(at,n):
        data=bytearray()
        for off in range(0,n,128):
            text=cmd(f'DBG m {at+off:x} {min(8,(n-off+15)//16):x}')
            for line in text.splitlines():
                match=re.match(r'^[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{4}\s+){1,8})',line)
                if match:data.extend(bytes.fromhex(match[1]))
        assert len(data)>=n;return bytes(data[:n])
    def long(at):return int.from_bytes(read(at,4),'big')
    task=long(long(4)+276);cli=long(task+172)*4;node=long(cli+60)*4;hunks=[]
    while node:hunks.append(node+4);node=long(node)*4;assert len(hunks)<=8
    assert len(hunks)==4;bss,syms=elf_symbols(ROOT/'amiga/out/bruce_amiga.elf')
    def address(name):return hunks[3]+syms[name]-bss
    m=address('m');assert read(m+0x29,1)==b'\x01','Use room2 in the private normal process'
    def write(at,value):cmd(f'DBG W {at:x} {value:02x}')
    component=read(m+0x276e,1)[0];second=read(m+0x2771,1)[0]
    enabled=read(m+0x2773+component,1)[0]
    if second<128:enabled|=read(m+0x2773+second,1)[0]
    writes={0x96:0x81,0x9f:128,0xa2:145,0xa5:1,0xc0:0,0xc3:0,0xcf:8,0xd2:15,0x107:200,0x4f49:2,0x4f4f:72,0x5e:255}
    for at,value in writes.items():write(m+at,value)
    write(m+0xd015,read(m+0xd015,1)[0]|enabled)
    def sample(label,active):
        time.sleep(2)
        dirty=[list(struct.unpack('>4h',read(address('actor_dirty')+buffer*40,8))) for buffer in range(2)]
        flags=read(m+0x96,1)[0];fault=int.from_bytes(read(address('source_fault'),2),'big')
        assert flags&1==int(active) and fault==0,(label,flags,fault)
        assert all((rect[2]>rect[0] and rect[3]>rect[1])==active for rect in dirty),(label,dirty)
        subprocess.run([sys.executable,str(ROOT/'tools/inspect_native_menu.py'),'--pid',str(a.pid),'--log',str(a.log),'--label',label],check=True,stdout=subprocess.DEVNULL)
        return dict(label=label,flags=flags,buffer_dirty=dirty,fault=fault)
    rows=[sample('yamo-visible',True)]
    write(m+0x96,0x80);write(m+0x5e,255);write(m+0xd015,read(m+0xd015,1)[0]&(~enabled&255))
    rows.append(sample('yamo-hidden',False))
    write(m+0x96,0x81);write(m+0xd015,read(m+0xd015,1)[0]|enabled)
    rows.append(sample('yamo-returned',True))
    artifacts=[]
    for row in rows:
        record=json.loads((ROOT/'reference/analysis/session-walls-2026-10-25'/(row['label']+'.json')).read_text())
        artifacts.extend(record['artifacts'])
    report=dict(status='passed_owned_native_visibility_lifecycle',binary=dict(path='amiga/out/bruce_amiga.exe',sha256=hashlib.sha256((ROOT/'amiga/out/bruce_amiga.exe').read_bytes()).hexdigest()),
        controlled_injection=True,natural_playthrough=False,room=2,source_actor=1,artifacts=artifacts,source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in ['tools/audit_native_visibility.py','core/session.c','core/c64_rooms.c']],method='Injected active bit, source wait and original component enable masks; actual normal draw loop and both buffer dirty rectangles',states=rows)
    out=ROOT/'reference/validation/source-visibility-native.json';out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
