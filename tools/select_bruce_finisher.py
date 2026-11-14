"""Convert a generated kiai into a short, one-page Enhanced Paula sample."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import wave

from build_enhanced_audio import BRUCE_FINISH, write_wav


def select(source, prompt):
    if BRUCE_FINISH.exists():raise SystemExit(f'Asset directory already exists: {BRUCE_FINISH}')
    # The selected take ends its phrase at 0.46 s. Compress time without
    # raising pitch, then use the existing 1,024-byte Paula voice page.
    filters='atrim=start=0:end=0.46,asetpts=PTS-STARTPTS,highpass=f=120,atempo=1.84,aresample=4000,apad=whole_len=1000,atrim=end_sample=1000'
    with tempfile.TemporaryDirectory(dir=BRUCE_FINISH.parent) as temp:
        stage=Path(temp)/BRUCE_FINISH.name;stage.mkdir()
        intermediate=Path(temp)/'converted.wav'
        subprocess.run(['ffmpeg','-v','error','-nostdin','-i',str(source),'-af',filters,
                        '-ac','1','-c:a','pcm_s16le',str(intermediate)],check=True)
        with wave.open(str(intermediate),'rb') as w:
            assert (w.getnchannels(),w.getframerate(),w.getsampwidth(),w.getnframes())==(1,4000,2,1000)
            pcm=list(struct.unpack('<1000h',w.readframes(1000)))
        mean=sum(pcm)/len(pcm);signal=[v-mean for v in pcm]
        for i in range(12):signal[i]*=i/11
        for i in range(80):signal[-80+i]*=(79-i)/79
        peak=max(abs(v) for v in signal);assert peak>100
        pcm=[round(v*28672/peak) for v in signal]
        target=stage/'bruce_finish.wav';write_wav(target,4000,pcm)
        shutil.copyfile(source,stage/'raw-kiai.wav')
        metadata=dict(generator='local AudioGen medium',prompt=prompt.read_text(encoding='utf-8').strip(),
            source_file='raw-kiai.wav',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            ffmpeg_filter=filters,rate=4000,samples=1000,duration_ms=250,peak=28672,
            fade_in_samples=12,fade_out_samples=80,
            selected_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
        (stage/'sources.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
        stage.rename(BRUCE_FINISH)
    print('Selected Bruce finisher: 250 ms, 1000 PCM bytes, 500 packed bytes.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('prompt',type=Path)
    args=parser.parse_args();select(args.source,args.prompt)
