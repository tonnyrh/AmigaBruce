"""Audit three source music voices and isolated native WinUAE recordings.

The IPC recorder uses unconverted PCM passthrough. Its AVI header describes
WinUAE's stale GUI workprefs (mono44100), not the live stereo48000 device.
Require the observed live format, PAL packet sizes and identical L/R mix
before rewrapping those unchanged bytes. Reject the earlier converted takes.
This is native Amiga PCM, not a recording of a SID or a natural playthrough.
"""
from pathlib import Path
import array
import argparse
import ctypes
import hashlib
import json
import math
import struct
import sys
import wave

from verify_source_audio import ROOT, SHA, State, Voice

OUT=ROOT/'reference/analysis/audio-playback-2026-10-25'
CAPTURE=ROOT/'.tmp/audio-playback-mixed'


def artifact(path):
    return dict(path=path.relative_to(ROOT).as_posix(),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                size_bytes=path.stat().st_size)


def packets(path):
    data=path.read_bytes();chunks=[];formats=[]
    assert data[:4]==b'RIFF' and data[8:12]==b'AVI '
    def scan(start,end):
        while start+8<=end:
            tag,size=struct.unpack_from('<4sI',data,start);at=start+8
            assert at+size<=end,(tag,size,end-at)
            if tag==b'LIST':scan(at+4,at+size)
            elif tag==b'strf':formats.append(struct.unpack_from('<HHIIHH',data,at))
            elif tag.endswith(b'wb'):chunks.append(data[at:at+size])
            start=at+size+(size&1)
    # The completed RIFF length excludes WinUAE's trailing allocation padding.
    scan(12,min(len(data),8+struct.unpack_from('<I',data,4)[0]))
    assert formats==[(1,1,44100,88200,2,16)],formats
    assert len(chunks)>=1155,'Capture must cover a whole source music loop'
    assert all(len(c) in (3844,3848) for c in chunks[2:-2]),'Not live stereo48000 PAL PCM'
    return chunks,formats[0]


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'report.json').exists():
        previous=json.loads((OUT/'report.json').read_text())
        current=hashlib.sha256((ROOT/'amiga/out/bruce_amiga.exe').read_bytes()).hexdigest()
        assert previous['normal_binary']['sha256']==current, 'Old captures belong to an archived build; make fresh native recordings before recording a new report'
    source=ROOT/'.reference/c64/work/untrained-memory.bin'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==SHA
    score=json.loads((ROOT/'assets/audio/c64-equivalent-v1/source-registers.json').read_text())
    libpath=ROOT/'.tmp/source-audio-test/audio.dll';lib=ctypes.CDLL(str(libpath))
    state=State();voices=(Voice*3)();lib.bl_source_audio_reset(ctypes.byref(state))
    bank=(ROOT/'assets/audio/c64-equivalent-v1/waveforms.pcm').read_bytes()
    metrics=[dict(paula_channel=c,active_fields=0,nonzero_pcm_fields=0,
                  first_active_field=None,minimum_hz=1e10,maximum_hz=0) for c in range(3)]
    for frame,row in enumerate(score['music']):
        lib.bl_source_audio_render(ctypes.byref(state),(ctypes.c_ubyte*26)(*row),voices)
        for c,v in enumerate(voices):
            if not v.volume:continue
            m=metrics[c];m['active_fields']+=1
            m['nonzero_pcm_fields']+=bool(any(bank[v.offset:v.offset+v.length]))
            if m['first_active_field'] is None:m['first_active_field']=frame
            hz=3546895/(v.period*v.length)
            m['minimum_hz']=min(m['minimum_hz'],hz);m['maximum_hz']=max(m['maximum_hz'],hz)
    assert lib.bl_source_audio_faults()==0
    assert [m['active_fields'] for m in metrics]==[970,338,610]
    assert all(m['nonzero_pcm_fields']==m['active_fields'] for m in metrics)
    for m in metrics:
        m['first_active_seconds_at_50hz']=m['first_active_field']/50
        m['minimum_hz']=round(m['minimum_hz'],3);m['maximum_hz']=round(m['maximum_hz'],3)

    log=CAPTURE/'winuaelog.txt';logtext=log.read_text(errors='replace')
    assert 'WASAPI: Shared Pull CH=2 FREQ=48000' in logtext
    assert 'Shared Pull CH=8' not in logtext,'Reject a surround fallback'
    cfg=CAPTURE/'capture.uae';settings=dict(line.split('=',1) for line in cfg.read_text().splitlines() if '=' in line)
    assert settings['sound_channels']=='stereo' and settings['sound_stereo_separation']=='0'
    assert settings['sound_frequency']=='48000'
    captures=[]
    for n,name,mask in ((1,'paula-0',1),(2,'paula-1',2),(3,'paula-2',4),(4,'mixed',7)):
        path=CAPTURE/f'output_{n}.avi';blocks,header=packets(path)
        raw=b''.join(blocks);pcm=array.array('h');pcm.frombytes(raw)
        if sys.byteorder!='little':pcm.byteswap()
        assert len(pcm)%2==0
        assert all(pcm[i]==pcm[i+1] for i in range(0,len(pcm),2)),'L/R mix differs'
        peak=max(abs(v) for v in pcm);rms=math.sqrt(sum(v*v for v in pcm)/len(pcm))
        assert peak>100 and rms>10,(name,peak,rms)
        dest=OUT/f'title-native-{name}.wav'
        with wave.open(str(dest),'wb') as w:
            w.setparams((2,2,48000,0,'NONE','NONE'));w.writeframes(raw[:26*192000])
        captures.append(dict(name=name,diagnostic_channel_mask=mask,
            complete_source_loops_minimum=1,pcm_packets=len(blocks),
            live_seconds=len(raw)/192000,peak=peak,rms=round(rms,3),
            left_right_identical=True,avi_header=list(header),
            method='Unconverted PCM passthrough rewrapped as live stereo48000; PAL packet sizes verified',
            native_capture=artifact(path),wav=artifact(dest)))
    clocka=json.loads((OUT/'title-clock-a.json').read_text(encoding='utf-8-sig'))
    clockb=json.loads((OUT/'title-clock-b.json').read_text(encoding='utf-8-sig'))
    def count(c):
        words=c['memory'].splitlines()[0].split();return int(words[2]+words[3],16)
    seconds=(clockb['qpc']-clocka['qpc'])/clocka['frequency']
    report=dict(status='scoped_native_three_voice_mix_verified',source_sha256=SHA,
        edition_verified=False,sid_analog_emulation=False,natural_playthrough=False,
        game_audio_code_changed=False,source_music_fields=len(score['music']),
        source_voice_metrics=metrics,native_captures=captures,
        normal_binary=artifact(ROOT/'amiga/out/bruce_amiga.exe'),
        normal_adf=artifact(ROOT/'amiga/out/bruce_amiga.adf'),
        emulator=artifact(CAPTURE/'winuae64.exe'),capture_config=artifact(cfg),
        output_profile=artifact(ROOT/'amiga/out/bruce-a500.uae'),
        music_clock=dict(native_fields=count(clockb)-count(clocka),host_seconds=seconds,
            fields_per_host_second=(count(clockb)-count(clocka))/seconds,
            method='Normal executable counter sampled through IPC; monotonic host QPC',
            measurement_files=[artifact(OUT/'title-clock-a.json'),artifact(OUT/'title-clock-b.json')]),
        user_feedback=dict(hard_pan_to_mono='Effects reported present; some timbres odd',
                           music='User still suspected a missing voice before corrected stereo mix'),
        limitations=['Diagnostic channel muting in owned emulator, not natural game input',
                     'Source/native outputs are audible; exact waveform/ADSR timing parity is not certified',
                     'Native parameter regression still tests only120 title fields',
                     'Rare long DMA waveform transitions and rendering-induced audio delays remain open',
                     'Converted earlier AVI takes have mismatched format and are excluded'],
        source_files=[artifact(ROOT/p) for p in ('tools/audit_audio_playback.py','amiga-run.ps1',
            'amiga/main.c','amiga/source_audio.h','core/source_audio.c','core/source_audio.h',
            'assets/audio/c64-equivalent-v1/source-registers.json','assets/audio/c64-equivalent-v1/waveforms.pcm')],
        live_log=artifact(log),host_library=artifact(libpath))
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS three native music voices and full mix audible on both outputs; correct PAL PCM packet rate')
    print('Source active fields:',[m['active_fields'] for m in metrics])
    print('Native RMS:',[(c['name'],c['rms']) for c in captures])


def verify():
    report=json.loads((OUT/'report.json').read_text())
    items=report['source_files']+[report[k] for k in
        ('normal_binary','normal_adf','emulator','capture_config','output_profile','live_log')]
    if not report.get('host_library_is_transient_provenance'):items.append(report['host_library'])
    items+=report['music_clock']['measurement_files']
    for capture in report['native_captures']:
        items += [capture['native_capture'],capture['wav']]
        assert capture['left_right_identical'] and capture['pcm_packets']>=1155
        assert capture['rms']>10 and capture['peak']>100
    for item in items:assert artifact(ROOT/item['path'])==item,f"Stale audio playback evidence: {item['path']}"
    assert [m['active_fields'] for m in report['source_voice_metrics']]==[970,338,610]
    assert [m['first_active_field'] for m in report['source_voice_metrics']]==[1,385,129]
    assert all(m['nonzero_pcm_fields']==m['active_fields'] for m in report['source_voice_metrics'])
    assert 49<report['music_clock']['fields_per_host_second']<51
    assert not report['edition_verified'] and not report['sid_analog_emulation']
    print('VERIFIED profile, source music voices and native PCM captures; '+
          ('recorded program is an archived historical build' if report.get('historical_build') else 'recorded normal build is current'))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    verify() if args.verify else main()
