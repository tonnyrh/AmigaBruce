"""Owned WinUAE diagnostic: send Amiga keys, reconstruct current bitplanes.

Uses WinUAE's public IPC/debug interface, not host keyboard injection.
Only the supplied PID may receive commands. This is UI inspection, not a
real-time test or a natural C64 recording.
"""
import argparse,hashlib,json,re,struct,time
from pathlib import Path
from winuae_ipc import command
from capture_paula_stream import elf_symbols
from preview_planar import render
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--log',type=Path);p.add_argument('--pipe')
    p.add_argument('--label',required=True);p.add_argument('--keys',default='');a=p.parse_args()
    pipe=a.pipe or re.findall(r"IPC: Named Pipe '([^']+)' open",a.log.read_text(errors='replace'))[-1]
    calls=[]
    def cmd(s):
        r=command(pipe,s,expected_pid=a.pid);calls.append(dict(command=s,result=r));return r
    def memory(at,n):
        data=bytearray()
        for off in range(0,n,16):
            count=min(16,n-off);s=cmd(f'DBG m {at+off:x} 1')
            block=bytearray()
            for line in s.splitlines():
                match=re.match(r'^[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{4}\s+){1,8})',line)
                if match:block.extend(bytes.fromhex(match[1]))
            assert len(block)>=count,s;data.extend(block[:count])
        return bytes(data)
    def long(at):return int.from_bytes(memory(at,4),'big')
    for key in filter(None,a.keys.split(',')):
        event='KEY_D' if key=='SHIFT_D' else 'KEY_'+key
        if key=='SHIFT_D':cmd('EVT KEY_SHIFT_LEFT 1');time.sleep(.3)
        cmd(f'EVT {event} 1');time.sleep(.35)
        cmd(f'EVT {event} 0');time.sleep(.4)
        if key=='SHIFT_D':cmd('EVT KEY_SHIFT_LEFT 0');time.sleep(.3)
    if a.keys:time.sleep(3)
    state=cmd('DBG c');copper=int(re.search(r'COP1LC: \$([0-9a-fA-F]+)',state)[1],16)
    words=struct.unpack('>34H',memory(copper,68));pointers=[]
    for plane in range(4):
        reg,hi,reg2,lo=words[18+4*plane:22+4*plane]
        assert (reg,reg2)==(0xe0+plane*4,0xe2+plane*4)
        pointers.append(hi*65536+lo)
    assert pointers==[pointers[0]+40*i for i in range(4)]
    folder=ROOT/'reference/analysis/session-walls-2026-10-25';folder.mkdir(parents=True,exist_ok=True)
    raw=folder/(a.label+'.bpl')
    assert ' ' not in str(raw),'This debugger version requires a path without spaces'
    saved=cmd(f'DBG S {raw} {pointers[0]:x} a000')
    assert 'Wrote ' in saved,saved
    assert raw.exists() and raw.stat().st_size==40960
    png=ROOT/'docs/images'/('session-'+a.label+'.png');render(raw,png,interleaved=True)
    # Locate current program BSS through the actual KS1.3 CLI module chain.
    task=long(long(4)+276);cli=long(task+172)*4;node=long(cli+60)*4;hunks=[]
    while node:
        assert len(hunks)<8;hunks.append(node+4);node=long(node)*4
    assert len(hunks)==4
    bss,syms=elf_symbols(ROOT/'amiga/out/bruce_amiga.elf');base=hunks[3]+syms['m']-bss
    m=memory(base+0x28,28)
    record=dict(label=a.label,normal_binary=dict(path='amiga/out/bruce_amiga.exe',sha256=hashlib.sha256((ROOT/'amiga/out/bruce_amiga.exe').read_bytes()).hexdigest()),
        source_room=m[1]+1,source_spare_falls=m[0],bitplanes=pointers,
        source_music_fields=long(hunks[3]+syms['source_music_fields']-bss),
        source_audio_mode=memory(hunks[3]+syms['source_audio_mode']-bss,1)[0],
        method='Read current Amiga bitplanes through owned WinUAE IPC; not a C64 capture',
        artifacts=[dict(path=x.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(x.read_bytes()).hexdigest()) for x in (raw,png)])
    (folder/(a.label+'.json')).write_text(json.dumps(record,indent=2)+'\n')
    (ROOT/'.tmp/session-ui'/(a.label+'-ipc.json')).write_text(json.dumps(calls,indent=2)+'\n')
    print(json.dumps(record,indent=2))
if __name__=='__main__':main()
