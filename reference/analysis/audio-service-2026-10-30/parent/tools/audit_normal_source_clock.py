"""Read normal native clock progression from an explicitly owned process.

This checks the native PAL timer seam, not original-C64 raster timing.
"""
import argparse,hashlib,json,re,time
from pathlib import Path
from winuae_ipc import command
from capture_paula_stream import elf_symbols
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--log',type=Path,required=True);args=p.parse_args()
    pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",args.log.read_text(errors='replace'))[-1]
    def read(at,n):
        text=command(pipe,f'DBG m {at:x} {(n+15)//16:x}',expected_pid=args.pid);data=bytearray()
        for line in text.splitlines():
            match=re.match(r'^[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{4}\s+){1,8})',line)
            if match:data.extend(bytes.fromhex(match[1]))
        assert len(data)>=n,(hex(at),text);return bytes(data[:n])
    def long(at):return int.from_bytes(read(at,4),'big')
    task=long(long(4)+276);cli=long(task+172)*4;node=long(cli+60)*4;hunks=[]
    while node:hunks.append(node+4);node=long(node)*4;assert len(hunks)<=8
    bss,syms=elf_symbols(ROOT/'amiga/out/bruce_amiga.elf');assert len(hunks)==4
    def address(name):return hunks[3]+syms[name]-bss
    def sample():
        at=address('m');epoch=int.from_bytes(read(address('actor_loading_epoch'),2),'big')
        before=long(address('game_field_last'));age=int.from_bytes(read(at+0x87,2),'little');after=long(address('game_field_last'))
        return dict(clock_before=before,clock_after=after,age=age,epoch=epoch,
            active_flags=list(read(at+0x95,3)),actor_states=list(read(at+0xbf,3)),
            spawn_events=int.from_bytes(read(address('actor_spawn_events'),2),'big'),
            steps=int.from_bytes(read(address('actor_logic_steps'),2),'big'),fault=int.from_bytes(read(address('source_fault'),2),'big'),
            waiting=read(address('actor_delay_pending'),1)[0] or read(address('actor_gameover_pending'),1)[0])
    samples=[sample()]
    for _ in range(3):time.sleep(2);samples.append(sample())
    pairs=[]
    for a,b in zip(samples,samples[1:]):
        if a['epoch']!=b['epoch'] or a['waiting'] or b['waiting']:continue
        ticks=(b['age']-a['age'])&65535;minimum=(b['clock_before']-a['clock_after'])&0xffffff;maximum=(b['clock_after']-a['clock_before'])&0xffffff
        # Debugger reads span source work; allow two field boundaries.
        assert minimum-2<=ticks<=maximum+2,(a,b,ticks,minimum,maximum)
        pairs.append(dict(source_fields=ticks,clock_min=minimum,clock_max=maximum,source_steps=b['steps']-a['steps']))
    assert pairs and all(x['source_fields']>0 for x in pairs) and all(x['fault']==0 for x in samples)
    report=dict(edition_verified=False,natural_playthrough=False,original_raster_phase_verified=False,
        method='Owned normal68000 run: actual PAL clock stamp versus source87/88 room clock; debugger reads, no source-memory injection',
        binary=dict(path='amiga/out/bruce_amiga.exe',sha256=hashlib.sha256((ROOT/'amiga/out/bruce_amiga.exe').read_bytes()).hexdigest()),
        samples=samples,pairs=pairs)
    out=ROOT/'reference/analysis/actor-chain-2026-10-26/normal-clock.json';out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
