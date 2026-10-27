"""Compare native SFX queues/registers with actual6502; render playable previews."""
from pathlib import Path
import sys,ctypes,json,hashlib,random,wave,math
from build_c64_audio import Memory,call,SOURCE,SHA,ROOT

class State(ctypes.Structure):
    _fields_=[('level',ctypes.c_ulong*3),('phase',ctypes.c_ubyte*3),('gate',ctypes.c_ubyte*3),
              ('music_regs',ctypes.c_ubyte*26),('music_wait',ctypes.c_ubyte),('music_cursor',ctypes.c_ushort)]
class Voice(ctypes.Structure):
    _fields_=[('offset',ctypes.c_ushort),('length',ctypes.c_ushort),('period',ctypes.c_ushort),('volume',ctypes.c_ushort)]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    lib=ctypes.CDLL(str(ROOT/'.tmp/source-audio-test/audio.dll'))
    for name in ('bl_c64_audio_request','bl_c64_read'):
        getattr(lib,name).argtypes=[ctypes.c_long]
    lib.bl_c64_test_write.argtypes=[ctypes.c_long,ctypes.c_long]
    lib.bl_c64_read.restype=ctypes.c_ubyte
    lib.bl_source_audio_chip_bytes.restype=ctypes.c_ulong
    b=SOURCE.read_bytes();assert sha(SOURCE)==SHA
    data=json.loads((ROOT/'assets/audio/c64-equivalent-v1/source-registers.json').read_text())
    chip=(ctypes.c_ubyte*lib.bl_source_audio_chip_bytes())();lib.bl_source_audio_copy(chip)
    assert bytes(chip)==(ROOT/'assets/audio/c64-equivalent-v1/waveforms.pcm').read_bytes()
    regs=(ctypes.c_ubyte*26)();voices=(Voice*3)();s=State()
    ranges=[(0xd400,0xd419),(0xeb00,0xeb03),(0xef70,0xef73),(0xf070,0xf073),(0xf6,0xfc),(0x2581,0x2584)]
    fields=0;commands=set();rng=random.Random(20261025)
    cases=[[(0,128+i)] for i in range(15)]
    cases+=[[(0,128+a),(0,128+c),(0,128+d),(1,128+e)] for a,c,d,e in
            ((0,1,2,3),(13,13,13,0),(0,0,0,14),(8,4,2,6))]
    cases.append([(i,rng.randrange(128,143)) for i in range(0,2400,3)])
    for events in cases:
        m=Memory(b);lib.bl_c64_reset();call(m,0x255e);lib.bl_c64_audio_reset()
        for lo,hi in ranges:
            for at in range(lo,hi):lib.bl_c64_test_write(at,m[at])
        duration=260 if len(events)<10 else 2600
        for frame in range(duration):
            for when,fx in events:
                if when==frame:call(m,0x2509,y=fx);lib.bl_c64_audio_request(fx)
            m.gates=0
            for pc in (0xeb03,0xef73,0xf073):call(m,pc)
            lib.bl_c64_audio_frame(regs)
            assert list(regs)==m[0xd400:0xd419]+[m.gates],(events[:4],frame,'registers')
            for lo,hi in ranges:
                assert bytes(lib.bl_c64_read(at) for at in range(lo,hi))==bytes(m[lo:hi]),(frame,hex(lo))
            lib.bl_source_audio_render(ctypes.byref(s),regs,voices)
            assert all(124<=v.period<=65535 and 0<=v.volume<=64 and v.length%2==0 and
                       v.offset+v.length<=len(chip) for v in voices)
            fields+=1
        assert lib.bl_c64_audio_faults()==0
        assert lib.bl_source_audio_faults()==0
    lib.bl_source_audio_reset(ctypes.byref(s))
    for row in data['music']+data['music'][data['music_loop_frame']:]:
        lib.bl_source_audio_music(ctypes.byref(s),regs)
        assert list(regs)==row,'Music delta/RLE/source loop differs'
        lib.bl_source_audio_render(ctypes.byref(s),regs,voices)
    assert lib.bl_source_audio_faults()==0

    # Offline preview uses the EXACT native Paula parameter renderer. It is
    # intentionally labelled an Amiga-equivalent preview, not SID recording.
    rate=22050
    def render(rows):
        lib.bl_source_audio_reset(ctypes.byref(s));phase=[0.,0.,0.];pcm=[];cursor=0
        for frame,row in enumerate(rows):
            rr=(ctypes.c_ubyte*26)(*row);lib.bl_source_audio_render(ctypes.byref(s),rr,voices)
            end=round((frame+1)*rate/50)
            for sample in range(cursor,end):
                value=0.
                for c,v in enumerate(voices):
                    phase[c]%=v.length
                    raw=chip[v.offset+int(phase[c])];raw=raw if raw<128 else raw-256
                    value+=raw*v.volume/64
                    phase[c]+=3546895/(v.period*rate)
                pcm.append(max(-32768,min(32767,round(value*85))))
            cursor=end
        assert any(pcm)
        return pcm
    out=ROOT/'assets/audio/c64-equivalent-v1'
    def save(name,pcm):
        import struct
        with wave.open(str(out/name),'wb') as w:
            w.setparams((1,2,rate,len(pcm),'NONE','not compressed'));w.writeframes(struct.pack('<'+'h'*len(pcm),*pcm))
    save('title-amiga.wav',render(data['music']))
    medley=[]
    for fx in range(15):
        rows=data['effects'][fx]
        pcm=render(rows+[[0]*26 for _ in range(6)])
        save(f'effect-{128+fx:02x}.wav',pcm);medley+=pcm+[0]*(rate//5)
    save('effects-amiga.wav',medley)
    report=dict(status='passed_scoped_source_audio_controls',source_sha256=SHA,
        edition_verified=False,natural_playthrough=False,source_cpu_fields_compared=fields,
        sfx_ids=15,queue_priority_scenarios=len(cases),music_frames_compared=len(data['music'])*2-data['music_loop_frame'],
        chip_bytes=len(chip),old_chip_bytes=4004,source_timing_and_registers_match=True,
        sid_analog_emulation=False,paula_parameters_checked=True,
        previews=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in sorted(out.glob('*.wav'))],
        source_files=[dict(path=p,sha256=sha(ROOT/p)) for p in
            ('tools/build_c64_audio.py','tools/verify_source_audio.py','core/source_audio.c','core/source_audio.h',
             'core/source_audio_data.h','core/game.h','core/source_wall.h','core/c64_sfx.h','core/c64_sound_data.h','core/c64_rooms.c','core/c64_rooms.h','test-source-audio.ps1')])
    (ROOT/'reference/validation/source-audio-host.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS{fields} source SFX fields/priority cases; two title passes; {len(chip)}Chip bytes; created native-parameter WAV previews')

if __name__=='__main__':main()
