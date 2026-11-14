"""Select local AudioGen takes, then pack approved mono WAVs for Enhanced Paula."""
import argparse
import hashlib
import json
import shutil
import struct
import tempfile
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'assets/audio/enhanced-v1'
YAMO_HITS = ROOT/'assets/audio/enhanced-yamo-hit-v2'
BRUCE_FINISH = ROOT/'assets/audio/enhanced-bruce-finish-v1'
APPROVED = ROOT/'assets/audio/enhanced-combat-v2'
LEVELS = (-120,-82,-55,-36,-23,-13,-6,0,0,6,13,23,36,55,82,120)
# Name, playback rate, maximum duration in ms, Paula volume.
CUES = (
    ('bruce_punch',8000,90,46), ('bruce_kick',8000,118,50),
    ('yamo_punch',7200,108,54), ('yamo_kick',7200,135,56),
    ('kage_punch',8000,88,43), ('kage_kick',8000,110,45),
    ('kage_blade',8000,450,49), ('yamo_hit',8000,110,54),
    ('bruce_shout',8000,1000,58),
)


def sample_path(name, variant):
    if name=='bruce_shout':return APPROVED/'bruce_shout.wav'
    if name=='kage_blade' or (name=='kage_kick' and variant==1):
        return APPROVED/f'{name}_{variant}.wav'
    return (YAMO_HITS if name=='yamo_hit' else OUT)/f'{name}_{variant}.wav'


def sample_pitch(name, variant):
    return 1.0 if name in ('bruce_shout','kage_blade') else (0.98,1.02)[variant]


def select_yamo(folder):
    """Import two new non-vocal AudioGen impacts without altering the v1 bank."""
    import numpy as np
    from scipy.signal import butter,resample_poly,sosfilt
    import soundfile as sf
    if YAMO_HITS.exists():raise SystemExit(f'Selected asset directory already exists: {YAMO_HITS}')
    prompt=(folder/'prompt.txt').read_text(encoding='utf-8').strip()
    sources=[]
    with tempfile.TemporaryDirectory(dir=YAMO_HITS.parent) as temp:
        stage=Path(temp)/YAMO_HITS.name
        (stage/'raw').mkdir(parents=True)
        for variant in range(2):
            source=folder/f'impact_{variant}.wav'
            signal,rate=sf.read(source,always_2d=True)
            signal=signal.mean(axis=1)
            signal=sosfilt(butter(2,95,btype='highpass',fs=rate,output='sos'),signal)
            signal=resample_poly(signal,8000,rate)
            count=880
            energy=np.r_[0,np.cumsum(signal*signal)]
            peak=int(np.argmax(energy[count:]-energy[:-count]))
            active=np.flatnonzero(np.abs(signal[peak:peak+count])>.15*np.max(np.abs(signal[peak:peak+count])))
            start=min(len(signal)-count,max(0,peak+int(active[0])-24))
            clip=signal[start:start+count].copy()
            clip-=clip.mean()
            clip[:16]*=np.linspace(0,1,16)
            clip[-160:]*=np.linspace(1,0,160)
            maximum=float(np.max(np.abs(clip)))
            if maximum<1e-5:raise ValueError(f'Empty take: {source}')
            pcm=np.rint(clip*(28672/maximum)).astype(np.int16)
            path=stage/f'yamo_hit_{variant}.wav'
            write_wav(path,8000,pcm.tolist())
            shutil.copyfile(source,stage/'raw'/source.name)
            sources.append(dict(name=path.stem,generator='local AudioGen medium',prompt=prompt,
                source_file='raw/'+source.name,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                source_rate=rate,highpass_hz=95,start_resampled=start,rate=8000,samples=count,
                fade_in_samples=16,fade_out_samples=160,peak=28672,
                selected_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        (stage/'sources.json').write_text(json.dumps(sources,indent=2)+'\n',encoding='utf-8')
        stage.rename(YAMO_HITS)


def write_wav(path, rate, samples):
    with wave.open(str(path),'wb') as w:
        w.setparams((1,2,rate,0,'NONE','not compressed'))
        w.writeframes(struct.pack(f'<{len(samples)}h',*samples))


def select(folder):
    """One-time import. The native build needs only the trimmed WAVs and stdlib."""
    import numpy as np
    from scipy.signal import butter,resample_poly,sosfilt
    import soundfile as sf
    if OUT.exists():raise SystemExit(f'Selected asset directory already exists: {OUT}')
    prompts=json.loads((folder/'prompts.json').read_text(encoding='utf-8-sig'))
    sources=[];selected=[]
    # Preserve the original v1 import path for its archived source prompts.
    for name,rate,ms,_ in CUES[:7]+(('yamo_cry',6200,155,57),):
        for variant in range(2):
            path=folder/f'{name}_{variant}.wav'
            audio,src_rate=sf.read(path,always_2d=True)
            audio=audio.mean(axis=1)
            # Slow the deep voice before cropping. Roll off its top end to
            # keep a short chest sound distinct from the swishing attacks.
            if name=='yamo_cry':
                audio=sosfilt(butter(3,1300,fs=src_rate,output='sos'),audio)
                speed=(70,75)[variant]
            else:
                speed=100
            # Discard sub-bass rumble before transient selection. It can
            # otherwise use most of the 4-bit range without an audible hit.
            cutoff={'bruce_punch':120,'bruce_kick':140,'kage_punch':150,
                    'kage_kick':240,'kage_blade':180,'yamo_cry':45}.get(name,75)
            audio=sosfilt(butter(2,cutoff,btype='highpass',fs=src_rate,output='sos'),audio)
            signal=resample_poly(audio,rate*100,src_rate*speed)
            count=2*round(rate*ms/2000)
            assert len(signal)>=count and count<=1024
            # Locate the most energetic complete phrase, then lead its first
            # audible transient by 3 ms. No silence at the start of a blow.
            energy=np.r_[0,np.cumsum(signal*signal)]
            peak=int(np.argmax(energy[count:]-energy[:-count]))
            if name=='yamo_cry':
                # Prefer the voiced chest sound to a louder breath at the
                # end of the take. Compare 60–150 Hz periodicity locally.
                def vocal_score(start):
                    v=signal[start+count//5:start+4*count//5]
                    power=float(np.dot(v,v))
                    corr=np.correlate(v,v,'full')[len(v)-1:]
                    periodic=max(corr[rate//150:rate//60+1])/max(1e-10,power)
                    return periodic*periodic*power**0.4
                peak=max(range(0,len(signal)-count+1,rate//100),key=vocal_score)
            section=signal[peak:peak+count]
            active=np.flatnonzero(np.abs(section)>.12*np.max(np.abs(section)))
            start=min(len(signal)-count,max(0,peak+int(active[0])-rate*3//1000))
            clip=signal[start:start+count].copy()
            clip-=clip.mean()
            fade=max(4,rate//400)
            clip[:fade]*=np.linspace(0,1,fade)
            release=rate//70
            clip[-release:]*=np.linspace(1,0,release)
            maximum=np.max(np.abs(clip))
            if maximum<1e-5:raise ValueError(f'Empty take: {path}')
            pcm=np.rint(clip*(28672/maximum)).astype(np.int16)
            selected.append((path.name,rate,pcm.tolist()))
            sources.append(dict(name=path.stem,prompt=prompts[name],generator='local AudioGen medium',
                                take_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                source_rate=src_rate,playback_speed_percent=speed,highpass_hz=cutoff,start_resampled=start))
    with tempfile.TemporaryDirectory(dir=OUT.parent) as temp:
        stage=Path(temp)/OUT.name
        stage.mkdir()
        for name,rate,pcm in selected:write_wav(stage/name,rate,pcm)
        (stage/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
        stage.rename(OUT)


def build(preview=None):
    packed=bytearray()
    long_pcm=bytearray()
    offsets={}
    rows=[]
    reel=[]
    for name,rate,_,volume in CUES:
        for variant in range(2):
            with wave.open(str(sample_path(name,variant)),'rb') as w:
                assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(rate,1,2)
                count=w.getnframes()
                samples=struct.unpack(f'<{count}h',w.readframes(count))
            assert 0<count<=8000 and count%2==0
            codes=[min(range(16),key=lambda i:abs(x-256*LEVELS[i])) for x in samples]
            pitch=sample_pitch(name,variant)
            period=round(3546895/(rate*pitch))
            # Long clips play directly from a Chip hunk. This avoids larger
            # per-voice work pages, streaming work and expansion-RAM growth.
            # Quantization matches the approved listening-page preview.
            direct=count>1024
            encoded=(bytes(LEVELS[c]&255 for c in codes) if direct else
                     bytes((a<<4)|b for a,b in zip(codes[::2],codes[1::2])))
            key=(direct,encoded)
            bank=long_pcm if direct else packed
            if key not in offsets:
                offsets[key]=len(bank);bank.extend(encoded)
            rows.append((offsets[key],count//2,period,volume))
            assert LEVELS[codes[0]]==LEVELS[codes[-1]]==0 and len(set(codes))>=7
            if preview:
                # Render at the actual Paula period and programmed volume.
                length=round(count*16000*period/3546895)
                reel.extend(LEVELS[codes[min(count-1,int(i*3546895/(period*16000)))]]*4*volume
                            for i in range(length))
                reel.extend([0]*(4000 if variant else 1600))
    # Each lookup expands one byte directly into a big-endian Paula word.
    words=[((LEVELS[i>>4]&255)<<8)|(LEVELS[i&15]&255) for i in range(256)]
    lines=['/* Generated by tools/build_enhanced_audio.py from the selected AudioGen WAVs. */',
           'enum { '+', '.join('FX_'+name.upper() for name,_,_,_ in CUES)+', FX_COUNT };',
           'static const struct { UWORD offset,words,period,volume; } foley_samples[]={']
    lines+=['{'+','.join(map(str,row))+'},' for row in rows]
    lines+=['};','static const UWORD foley_expand[256]={']
    lines += [','.join(f'0x{v:04x}' for v in words[i:i+12])+',' for i in range(0,len(words),12)]
    lines+=['};','static const UBYTE foley_bank[]={']
    lines += [','.join(map(str,packed[i:i+24]))+',' for i in range(0,len(packed),24)]
    lines+=['};', '#ifdef __m68k__',
            '#define FOLEY_CHIP __attribute__((section(".MEMF_CHIP"),aligned(2)))',
            '#else', '#define FOLEY_CHIP', '#endif',
            'static const UBYTE foley_long_pcm[] FOLEY_CHIP={']
    lines += [','.join(map(str,long_pcm[i:i+24]))+',' for i in range(0,len(long_pcm),24)]
    lines+=['};','#undef FOLEY_CHIP','']
    header=ROOT/'amiga/enhanced_audio_data.h'
    content='\n'.join(lines)
    if not header.exists() or header.read_text()!=content:header.write_text(content,encoding='ascii')
    if preview:
        if preview.exists():raise SystemExit(f'Preview already exists: {preview}')
        write_wav(preview,16000,reel)
    print(f'Enhanced combat: {len(rows)} playback entries, {len(offsets)} unique samples, {len(packed)} packed bytes, {len(long_pcm)} direct Chip bytes; source voice pages remain 1024 bytes')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--select',type=Path)
    parser.add_argument('--select-yamo',type=Path,help='Import two new impact takes plus prompt.txt into the v2 Yamo bank')
    parser.add_argument('--preview',type=Path)
    args=parser.parse_args()
    if args.select:select(args.select)
    if args.select_yamo:select_yamo(args.select_yamo)
    build(args.preview)
