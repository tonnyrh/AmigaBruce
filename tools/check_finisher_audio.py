"""Verify Bruce's finishing cry in an owned normal-ADF WinUAE instance.

Positions and enemy health are controlled starting conditions. Ordinary Fire
then drives source punch/contact/damage; no hit, kill or cry event is injected.
A winning or losing sound-choice seed is set before each knockout. Ordinary
empty swings must not advance that generator. A final isolated sample check
is explicitly a controlled playback request.
"""
import argparse
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
        p=folder/name;assert 'Wrote ' in cmd(f'DBG S {p} {at:x} {n:x}')
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
    assert not val(addr('foley_active'),1) and not val(addr('finisher_observer'))
    key('F4');wait(lambda:front()==reference(enhanced=True))
    tap_fire(cmd);wait(lambda:val(addr('game_field_active'),1))
    assert val(addr('foley_active'),1) and val(addr('finisher_observer'))
    ram=addr('m');cue=next(i for i,c in enumerate(CUES) if c[0]=='bruce_shout')
    records=[]
    key('P');wait(lambda:not val(addr('source_audio_active'),1))
    for actor in (1,2):put(ram+0x95+actor,0)
    put(ram+0x5d,255);put(ram+0x5e,255)
    cmd(f'DBG W {addr("foley_random"):x} 00 06')
    cmd(f'DBG W {addr("foley_played_mask"):x} 00 00 00 00')
    cmd('EVT JOY2_FIRE_BUTTON 1')
    try:
        key('P');wait(lambda:val(addr('foley_played_mask'))&3)
        time.sleep(.6)
    finally:cmd('EVT JOY2_FIRE_BUTTON 0')
    assert not val(addr('foley_played_mask'))&(3<<(2*cue))
    assert val(addr('foley_random'),2)==6
    records.append(dict(case='Ordinary empty swings',shout=False,random_unchanged=True))
    print('PASS ordinary swings cannot request a cry',flush=True)
    for victim,seed,selected in ((1,2,False),(1,6,True),(2,2,False),(2,6,True)):
        # Start each controlled case through the menu so no damage latch,
        # death delay or previous contact cache leaks from another knockout.
        key('F10');wait(lambda:front()==reference(enhanced=True))
        tap_fire(cmd);wait(lambda:val(addr('game_field_active'),1))
        # Let the source spawn routine install both VIC-slot -> actor maps.
        # Merely setting an enemy active before its first spawn leaves $4F40
        # at $FF, so real pixel contacts cannot reach that actor.
        wait(lambda:val(ram+0x96,1)&1 and val(ram+0x97,1)&1,60)
        key('P');wait(lambda:not val(addr('source_audio_active'),1))
        memory=dump('before.bin',ram,65536);floor=memory[0xa1]
        # Standard ground positions in room 1; other enemy waits off-screen.
        for actor in range(3):
            active=actor in (0,victim)
            values={0x95+actor:(1 if actor==0 else 0x81 if actor==1 else 0x41) if active else 0,
                    0x9e+actor:80 if actor==0 else 88,0xa1+actor:floor,
                    0xa4+actor:1 if actor==0 else 0,0xbf+actor:0,0xc2+actor:0,
                    0xce+actor:0 if actor==0 else 24,0x106+actor:0 if actor==0 else 24,
                    0xd1+actor:36 if actor==0 else 2,0x4fdb+actor:0}
            for at,n in values.items():put(ram+at,n)
        put(ram+0x5d,255);put(ram+0x5e,255)
        cmd(f'DBG W {addr("foley_random"):x} 00 {seed:02x}')
        cmd(f'DBG W {addr("foley_played_mask"):x} 00 00 00 00')
        cmd('EVT JOY2_FIRE_BUTTON 1')
        try:
            key('P');wait(lambda:val(addr('source_audio_active'),1))
            # The death handler can replace the negative health byte before
            # IPC observes it. Only the source knockout observer advances
            # this sound-choice state; observe that durable event instead.
            wait(lambda:val(addr('foley_random'),2)!=seed,30)
            if selected:wait(lambda:val(addr('foley_played_mask'))&(3<<(2*cue)),5)
        finally:cmd('EVT JOY2_FIRE_BUTTON 0')
        time.sleep(1.2)  # Let a selected one-second cry finish before the next case.
        assert not val(addr('source_fault'),2)
        assert bool(val(addr('foley_played_mask'))&(3<<(2*cue)))==selected
        assert val(addr('foley_random'),2)==(3 if selected else 1)
        snapshot=dump(f'victim-{victim}.bin',ram,65536)
        records.append(dict(victim=victim,input='Fire only',starting_health=2,controlled_random_seed=seed,shout=selected,
            observed_mask=val(addr('foley_played_mask')),observed_health=snapshot[0xd1+victim]))
        print('PASS source punch knockout:',('Yamo' if victim==1 else 'Kage'),'shout',selected,flush=True)

    key('P');wait(lambda:not val(addr('source_audio_active'),1))
    root=Path(__file__).resolve().parents[1]
    page=hunks[elf_hunk_index(folder/'release.elf','.MEMF_CHIP')]+5600
    with wave.open(str(sample_path('bruce_shout',0)),'rb') as w:
        n=w.getnframes();samples=struct.unpack(f'<{n}h',w.readframes(n))
    expected=bytes(min(LEVELS,key=lambda v:abs(s-256*v))&255 for s in samples)
    try:
        cmd(f'DBG W {addr("foley_played_mask"):x} 00 00 00 00')
        put(addr('source_audio_active'),1);put(addr('foley_voice')+1,2+cue)
        wait(lambda:val(addr('foley_played_mask'))&(3<<(2*cue)),15)
        assert dump('finish.pcm',page,n)==expected
        assert val(addr('foley_voice')+4,2)==round(3546895/8000)
        wait(lambda:val(addr('foley_voice')+3,1)==2,5)
    finally:put(addr('source_audio_active'),0)
    # Restoring Classic must detach the finishing observer as well as PCM.
    key('F10');wait(lambda:front()==reference(enhanced=True))
    key('F4');tap_fire(cmd);wait(lambda:val(addr('game_field_active'),1))
    assert not val(addr('foley_active'),1) and not val(addr('finisher_observer'))
    (folder/'result.json').write_text(json.dumps(dict(method=__doc__,checks=records,
        pcm_bytes_matched=n,classic_observer_detached=True),indent=2)+'\n')
    print('PASS 8000-byte Paula sample and Classic observer detach.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path);parser.add_argument('pid',type=int)
    args=parser.parse_args();check(args.folder.resolve(),args.pid)
