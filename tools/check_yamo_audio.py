"""Check both Enhanced Yamo impacts in an owned normal-ADF WinUAE instance.

Actors are paused and the real Paula service is given controlled cue requests.
This checks asset delivery, not a naturally played combat encounter.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import time
import wave

from build_enhanced_audio import CUES, LEVELS, sample_path
from capture_paula_stream import elf_symbols, elf_hunk_index
from title_reference import reference
from winuae_ipc import command, tap_fire


def check(folder, pid):
    pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",(folder/'winuaebootlog.txt').read_text(errors='replace'))[-1]
    def cmd(s):return command(pipe,s,timeout=10,expected_pid=pid)
    def val(at,n=4):
        match=re.search(r'(?mi)^[0-9a-f]{8}\s+((?:[0-9a-f]{4}\s+){1,8})',cmd(f'DBG m {at:x} 1'))
        return int.from_bytes(bytes.fromhex(match[1])[:n],'big')
    def dump(name,at,n):
        p=folder/name
        assert 'Wrote ' in cmd(f'DBG S {p} {at:x} {n:x}')
        return p.read_bytes()
    def front():
        at=int(re.search(r'COP1LC: \$([0-9a-f]+)',cmd('DBG c'),re.I)[1],16)
        w=struct.unpack('>66H',dump('copper.bin',at,132))
        if w[:2]!=(0x100,0x4200) or w[18:26:2]!=(0xe0,0xe2,0xe4,0xe6):return b''
        return dump('front.bpl',w[19]*65536+w[21],40960)
    def wait(fn,seconds=120):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if fn():return
            time.sleep(.12)
        raise AssertionError('Timed out: '+fn.__name__)
    def key(k):
        cmd('EVT KEY_'+k+' 1');time.sleep(.25);cmd('EVT KEY_'+k+' 0')
    def put(at,n):cmd(f'DBG W {at:x} {n:02x}')

    wait(lambda:front()==reference(),240)
    task=val(val(4)+276);cli=val(task+172)*4;node=val(cli+60)*4;hunks=[]
    while node:
        hunks.append(node+4);node=val(node)*4;assert len(hunks)<=8
    bss,symbols=elf_symbols(folder/'release.elf')
    bss_hunk=elf_hunk_index(folder/'release.elf')
    def addr(name):return hunks[bss_hunk]+symbols[name]-bss
    assert not val(addr('foley_active'),1)
    key('F4');wait(lambda:front()==reference(enhanced=True))
    tap_fire(cmd);wait(lambda:val(addr('game_field_active'),1))
    assert val(addr('foley_active'),1)==1
    key('P');wait(lambda:not val(addr('source_audio_active'),1))
    # Use the existing 1024-byte voice page; no additional Chip allocation.
    root=Path(__file__).resolve().parents[1]
    page=val(addr('sfx_pcm'))+int(re.search(r'BL_SOURCE_AUDIO_CHIP_BYTES (\d+)',
        (root/'core/source_audio_data.h').read_text())[1])
    cue=next(i for i,c in enumerate(CUES) if c[0]=='yamo_hit')
    records=[]
    try:
        put(addr('source_audio_active'),1)
        for _ in range(2):
            variant=val(addr('foley_variant')+cue,1)
            with wave.open(str(sample_path('yamo_hit',variant)),'rb') as w:
                n=w.getnframes();samples=struct.unpack(f'<{n}h',w.readframes(n))
            expected=bytes(min(LEVELS,key=lambda v:abs(s-256*v))&255 for s in samples)
            put(addr('foley_voice')+1,2+cue)
            wait(lambda:dump(f'variant-{variant}.pcm',page,n)==expected,15)
            period=round(3546895/(8000*(.98 if not variant else 1.02)))
            assert val(addr('foley_voice')+4,2)==period
            assert val(addr('foley_played_mask'),4)&(1<<(2*cue+variant))
            assert not val(addr('source_fault'),2)
            records.append(dict(variant=variant,pcm_bytes=n,period=period,
                pcm_sha256=hashlib.sha256(expected).hexdigest(),matched=True))
            print('PASS Yamo impact',variant,': 880 Paula bytes and period match.',flush=True)
            time.sleep(.25)
    finally:
        put(addr('source_audio_active'),0)
    assert {r['variant'] for r in records}=={0,1}
    (folder/'result.json').write_text(json.dumps(dict(method=__doc__,checks=records),indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path);parser.add_argument('pid',type=int)
    args=parser.parse_args();check(args.folder.resolve(),args.pid)
