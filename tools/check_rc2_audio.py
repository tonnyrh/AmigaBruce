"""RC2 audio checks in an owned normal-ADF WinUAE instance.

Ordinary held Fire exercises random punch selection. Paused-game direct
requests separately verify each approved clip, its PCM bytes and DMA end.
These controlled playback requests are not natural combat/progression tests.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import time
import wave

from build_enhanced_audio import CUES, LEVELS, sample_path, sample_pitch
from capture_paula_stream import elf_symbols, elf_hunk_index
from title_reference import reference
from winuae_ipc import command, tap_fire


def check(folder, pid):
    pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",(folder/'winuaebootlog.txt').read_text(errors='replace'))[-1]
    elf=folder/'release.elf'
    def cmd(s):return command(pipe,s,timeout=10,expected_pid=pid)
    def val(at,n=4):
        match=re.search(r'(?mi)^[0-9a-f]{8}\s+((?:[0-9a-f]{4}\s+){1,8})',cmd(f'DBG m {at:x} 1'))
        return int.from_bytes(bytes.fromhex(match[1])[:n],'big')
    def dump(name,at,n):
        p=folder/name;assert 'Wrote ' in cmd(f'DBG S {p} {at:x} {n:x}')
        return p.read_bytes()
    def front():
        c=int(re.search(r'COP1LC[:\s$]+([0-9a-f]+)',cmd('DBG c'),re.I)[1],16)
        w=struct.unpack('>66H',dump('copper.bin',c,132))
        if w[:2]!=(0x100,0x4200) or w[18:26:2]!=(0xe0,0xe2,0xe4,0xe6):return b''
        return dump('front.bpl',w[19]*65536+w[21],40960)
    def wait(fn,seconds=30):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if fn():return
            time.sleep(.02)
        raise AssertionError('Timed out: '+fn.__name__)
    def key(k):
        cmd('EVT KEY_'+k+' 1');time.sleep(.20);cmd('EVT KEY_'+k+' 0')
    def put(at,n,width=1):cmd(f'DBG W {at:x} '+n.to_bytes(width,'big').hex(' '))

    wait(lambda:front()==reference(),240)
    task=val(val(4)+276);cli=val(task+172)*4;node=val(cli+60)*4;hunks=[]
    while node:
        hunks.append(node+4);node=val(node)*4;assert len(hunks)<=8
    bss,symbols=elf_symbols(elf);bss_hunk=elf_hunk_index(elf)
    def addr(name):return hunks[bss_hunk]+symbols[name]-bss
    assert not val(addr('foley_active'),1) and not val(addr('sound_observer'))
    assert 0xc00000<=hunks[bss_hunk]<0xc80000, 'Working data spilled into Chip RAM'
    chip_hunk=elf_hunk_index(elf,'.MEMF_CHIP')
    assert hunks[chip_hunk]<0x80000
    memory=[];node=val(val(4)+322)  # KS1.3 ExecBase.MemList
    while val(node):
        largest=0;chunk=val(node+16)
        while chunk:
            largest=max(largest,val(chunk+4));chunk=val(chunk)
        memory.append(dict(attributes=val(node+14,2),lower=hex(val(node+20)),upper=hex(val(node+24)),
                           free=val(node+28),largest=largest))
        node=val(node)
    key('F4');wait(lambda:front()==reference(enhanced=True))
    # Normal menu options, not injected invulnerability or actor coordinates.
    cmd('EVT KEY_SHIFT_LEFT 1')
    try:key('D')
    finally:cmd('EVT KEY_SHIFT_LEFT 0')
    key('F1');key('F2');key('F5');tap_fire(cmd)
    wait(lambda:val(addr('game_field_active'),1))
    assert val(addr('foley_active'),1) and not val(addr('finisher_observer'))
    shout=next(i for i,c in enumerate(CUES) if c[0]=='bruce_shout')
    cmd('EVT JOY2_FIRE_BUTTON 1')
    try:
        wait(lambda:(val(addr('foley_played_mask'))&3) and
                    (val(addr('foley_played_mask'))&(3<<(2*shout))),35)
    finally:cmd('EVT JOY2_FIRE_BUTTON 0')
    ordinary=dict(input='Held primary Fire, menu invincibility enabled',mask=val(addr('foley_played_mask')),
                  source_fault=val(addr('source_fault'),2))
    assert not ordinary['source_fault']
    key('P');wait(lambda:not val(addr('source_audio_active'),1))
    # Reactivate only the audio service while the game stays in its pause loop.
    put(addr('source_audio_active'),1);time.sleep(1.2)
    records=[]
    try:
        for name,variant in [('kage_blade',0),('kage_blade',1),('kage_kick',1),('bruce_shout',0)]:
            cue=next(i for i,c in enumerate(CUES) if c[0]==name)
            with wave.open(str(sample_path(name,variant)),'rb') as w:
                rate=w.getframerate();n=w.getnframes();samples=struct.unpack(f'<{n}h',w.readframes(n))
            expected=bytes(min(LEVELS,key=lambda v:abs(s-256*v))&255 for s in samples)
            put(addr('foley_played_mask'),0,4);put(addr('foley_variant')+cue,variant)
            put(addr('foley_voice')+1,2+cue)
            wait(lambda:val(addr('foley_played_mask'))&(1<<(2*cue+variant)))
            started=time.monotonic();voice=addr('foley_voice')
            period=round(3546895/(rate*sample_pitch(name,variant)))
            assert val(voice+4,2)==period
            if n>1024:
                # This section contains only the three direct clips, ordered
                # Kage quick, Kage broad, Bruce shout by the production packer.
                offset={('kage_blade',0):0,('kage_blade',1):2000,('bruce_shout',0):5600}[name,variant]
                pcm=hunks[chip_hunk]+offset
            else:
                root=Path(__file__).resolve().parents[1]
                size=int(re.search(r'BL_SOURCE_AUDIO_CHIP_BYTES (\d+)',(root/'core/source_audio_data.h').read_text())[1])
                pcm=val(addr('sfx_pcm'))+size
            assert dump(name+f'-{variant}.pcm',pcm,n)==expected
            wait(lambda:val(voice+3,1)==2,3)
            elapsed=time.monotonic()-started
            expected_seconds=n*period/3546895
            assert elapsed<expected_seconds+.6
            # A delayed first IRQ would loop the clip instead of one-shot silence.
            hardware=cmd('DBG c');(folder/(name+f'-{variant}-paula.txt')).write_text(hardware)
            records.append(dict(name=name,variant=variant+1,pcm_bytes=n,period=period,
                                pcm_sha256=hashlib.sha256(expected).hexdigest(),
                                expected_seconds=expected_seconds,observed_end_seconds=elapsed))
            print('PASS native PCM and one-shot:',name,variant+1,n,'bytes',flush=True)
        assert not val(addr('source_fault'),2) and not val(addr('source_dma_faults'),2)
    finally:put(addr('source_audio_active'),0)
    key('F10');wait(lambda:front()==reference(enhanced=True,infinite=True,invincible=True))
    key('F4');tap_fire(cmd);wait(lambda:val(addr('game_field_active'),1))
    assert not val(addr('foley_active'),1) and not val(addr('sound_observer'))
    report=dict(method=__doc__,hunks=[hex(v) for v in hunks],memory=memory,
                bss_in_expansion_ram=True,long_pcm_in_chip_ram=True,ordinary_fire=ordinary,
                clips=records,classic_observer_detached=True,physical_listening_accepted=False)
    (folder/'audio.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS RC2 audio and return to Classic',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('pid',type=int)
    a=p.parse_args();check(a.folder.resolve(),a.pid)
