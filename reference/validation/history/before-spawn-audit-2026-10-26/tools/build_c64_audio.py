"""Extract source audio instructions/register traces, then make Paula resources.

No guessed notes or AI audio: execute the frozen music/SFX routines read-only.
Paula timbre/envelopes are a documented compact approximation, not SID emulation.
"""
from pathlib import Path
import sys, hashlib, json, math, wave, struct

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
SOURCE=ROOT/'.reference/c64/work/untrained-memory.bin'
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
SID_CLOCK=985248
PAULA_CLOCK=3546895
ATTACK_MS=[2,8,16,24,38,56,68,80,100,250,500,800,1000,3000,5000,8000]
RELEASE_MS=[6,24,48,72,114,168,204,240,300,750,1500,2400,3000,9000,15000,24000]

class Memory(list):
    def __init__(self,b):super().__init__(b);self.gates=0;self.writes=[]
    def __setitem__(self,k,v):
        if isinstance(k,int):
            if 0xd400<=k<=0xd418:
                self.writes.append((k,v))
                if k in (0xd404,0xd40b,0xd412) and v&1 and not self[k]&1:
                    self.gates |= 1<<((k-0xd404)//7)
        super().__setitem__(k,v)

def call(m,pc,y=0):
    c=MPU(memory=m,pc=pc);c.y=y;c.sp=0xfd;c.stPushWord(0x2fe)
    for n in range(50000):
        if c.pc==0x2ff:return
        c.step()
    raise RuntimeError(f'Source audio escaped ${c.pc:04X}')

def arr(name,data,ctype='unsigned char'):
    return f'static const {ctype} {name}[]={{\n'+''.join(','.join(map(str,data[i:i+24]))+',\n' for i in range(0,len(data),24))+'};\n'

def source_traces(b):
    effects=[];keys=set();freqs={0};records=[]
    for fx in range(15):
        m=Memory(b);call(m,0x255e);call(m,0x2509,y=128+fx);rows=[]
        for f in range(2000):
            m.gates=0;m.writes=[]
            for pc in (0xeb03,0xef73,0xf073):call(m,pc)
            rows.append(m[0xd400:0xd419]+[m.gates])
            if not(m[0xeb00]|m[0xef70]|m[0xf070]):break
        else:raise AssertionError(f'Unterminated effect {fx}')
        effects.append(rows)
        pointer=b[0xebe5+fx*2]|b[0xebe6+fx*2]<<8
        records.append(dict(id=hex(128+fx),stream_address=f'${pointer:04X}',frames=len(rows),priority=b[0x2572+fx]))
    m=Memory(b);m[0xe30a]=0;call(m,0xe000)
    m[0xe314]=3;m[0xe870]=0;m[0xe871]=255;call(m,0xe003)
    music=[];seen={}
    for f in range(10000):
        state=bytes(m[0xe000:0xeb00]+m[0xd400:0xd419])
        if state in seen:loop=seen[state];break
        seen[state]=f;m.gates=0;m.writes=[];call(m,0xe006)
        music.append(m[0xd400:0xd419]+[m.gates])
    else:raise AssertionError('No source title loop')
    for row in music+[r for e in effects for r in e]:
        for c in (0,7,14):
            keys.add((row[c+4]&0xf0,(row[c+2]|row[c+3]<<8)&4095));freqs.add(row[c]|row[c+1]<<8)
        assert row[0x17]==0,'A source filter route requires a separate conversion'
        assert not any(row[c+4]&6 for c in (0,7,14)),'Source sync/ring requires separate conversion'
    return effects,music,loop,records,keys,freqs

def build():
    out=ROOT/'assets/audio/c64-equivalent-v1';out.mkdir(parents=True,exist_ok=True)
    b=SOURCE.read_bytes();assert hashlib.sha256(b).hexdigest()==SHA
    effects,music,loop,records,keys,freqs=source_traces(b)
    # Cartesian waveform/PW variants also cover effects inheriting a previous
    # effect's pulse width. The original SFX player does not reset ADSR/PW.
    widths=sorted({pw for wf,pw in keys}|{0})
    variants=[(wf,pw) for wf in (16,32,64,80) for pw in (widths if wf in (64,80) else [0])]
    bank=bytearray();waves=[]
    for wf,pw in variants:
        for length in (8,16,32):
            values=[]
            for i in range(length):
                phase=i*4096//length
                tri=phase*2 if phase<2048 else (4095-phase)*2
                val=tri if wf==16 else phase if wf==32 else (4095 if phase>=pw else 0)
                if wf==80:val=tri & (4095 if phase>=pw else 0)
                values.append(val)
            mean=sum(values)/length;peak=max(1,max(abs(x-mean) for x in values))
            raw=bytes(round((x-mean)*120/peak)&255 for x in values)
            waves.append((wf,pw,length,len(bank)));bank.extend(raw)
    noise_offset=len(bank);lfsr=0x7ffff8
    # Deterministic broad-band Paula noise resource. This is not an exact SID
    # noise oscillator/analog filter; its pitch follows the source frequency.
    for i in range(1024):
        lfsr=((lfsr<<1)|(((lfsr>>22)^(lfsr>>17))&1))&0x7fffff
        bank.append(((lfsr>>8)&255))
    bank.extend(b'\0\0\0\0')
    assert len(bank)<=4004, f'Audio exceeds previous Chip allocation: {len(bank)}'
    frequency=[]
    for fn in sorted(freqs):
        hz=fn*SID_CLOCK/16777216
        length=32 if hz<=750 else 16 if hz<=1500 else 8
        period=65535 if not hz else max(124,min(65535,round(PAULA_CLOCK/(hz*length))))
        noise=65535 if not hz else max(124,min(65535,round(PAULA_CLOCK/(hz*16))))
        frequency.append((fn,period,length,noise))
    # RLE snapshots; split at the exact source loop seam.
    packets=[];loop_packet=None
    for frame,row in enumerate(music):
        if frame==loop:loop_packet=len(packets)
        if packets and packets[-1][1:]==row and packets[-1][0]<255 and frame!=loop:
            packets[-1][0]+=1
        else:packets.append([1]+row)
    assert loop_packet is not None
    blob=[];previous=[0]*25;loop_offset=None
    for i,packet in enumerate(packets):
        count,*row=packet
        if i==loop_packet:loop_offset=len(blob)
        changed=[j for j in range(25) if row[j]!=previous[j] or i in (0,loop_packet)]
        mask=sum(1<<j for j in changed)
        blob += [count,row[25]]+list(mask.to_bytes(4,'little'))+[row[j] for j in changed]
        previous=row[:25]
    header='/* Generated from frozen C64 source; see assets/audio/c64-equivalent-v1/manifest.json. */\n'
    header+=f'#define BL_SOURCE_AUDIO_CHIP_BYTES {len(bank)}\n#define BL_SOURCE_NOISE_OFFSET {noise_offset}\n'
    header+=f'#define BL_SOURCE_NOISE_BYTES 1024\n#define BL_SOURCE_MUSIC_BYTES {len(blob)}\n#define BL_SOURCE_MUSIC_LOOP {loop_offset}\n'
    header+=f'#define BL_SOURCE_WAVES {len(waves)}\n#define BL_SOURCE_FREQUENCIES {len(frequency)}\n'
    header+=arr('bl_source_wave_bytes',bank)
    header+='static const unsigned short bl_source_waves[][4]={'+','.join('{'+','.join(map(str,v))+'}' for v in waves)+'};\n'
    header+='static const unsigned short bl_source_frequencies[][4]={'+','.join('{'+','.join(map(str,v))+'}' for v in frequency)+'};\n'
    header+=arr('bl_source_music',blob)
    # Q16 full-scale increments per50Hz field, scaled from1MHz SID datasheet.
    header+=arr('bl_source_attack_step',[max(1,round(65535*20*SID_CLOCK/(1000000*t))) for t in ATTACK_MS],'unsigned long')
    header+=arr('bl_source_release_step',[max(1,round(65535*20*SID_CLOCK/(1000000*t))) for t in RELEASE_MS],'unsigned long')
    (ROOT/'core/source_audio_data.h').write_text(header,encoding='ascii')
    # Only source data read by the native SFX decoder; no6502 code shipped.
    raw=b[0xebe5:0xef70]
    h='/* Source $EBE5-$EF6F tables/streams and note tables; no opcode interpreter. */\n'
    h+=arr('bl_source_sfx_data',raw)+arr('bl_source_sfx_freq_lo',b[0xe200:0xe256])+arr('bl_source_sfx_freq_hi',b[0xe254:0xe2aa])
    (ROOT/'core/c64_sound_data.h').write_text(h,encoding='ascii')
    (out/'waveforms.pcm').write_bytes(bank)
    trace=dict(source_sha256=SHA,music_loop_frame=loop,music=music,effects=effects)
    (out/'source-registers.json').write_text(json.dumps(trace,separators=(',',':'))+'\n')
    manifest=dict(source=dict(path=SOURCE.relative_to(ROOT).as_posix(),sha256=SHA),edition_verified=False,
        method='Actual6502 music/SFX subroutines with controlled initialization; not natural full-machine play',
        music=dict(init='$E000 then $E003',play='$E006 per PAL field',caller='$06DA/$154C',
                   frames=len(music),loop_frame=loop,loop_length=len(music)-loop,packets=len(packets),bytes=len(blob),loop_byte=loop_offset),
        effects=records,priority_routine='$2509-$255D',drivers=['$EB03','$EF73','$F073'],
        waveform_bytes=len(bank),previous_sfx_chip_bytes=4004,source_sid_clock=SID_CLOCK,paula_clock=PAULA_CLOCK,
        paula_minimum_period=124,noise_source='deterministic23-bit LFSR Paula resource',
        envelopes='50Hz fixed-point piecewise linear approximation using MOS6581 ADSR rates',
        limitations=['Not analog SID/filter/noise or cycle-exact ADSR emulation',
                     '8/16/32-sample wave cycles quantize pulse width and Paula period',
                     'Noise sample rate constrained by OCS DMA; inaudible extremes cannot retain exact SID pitch',
                     'Source PAL cadence adapted to A500 fields; long-term clock mismatch remains open'],
        code_ranges=[dict(start=f'${lo:04X}',end_exclusive=f'${hi:04X}',sha256=hashlib.sha256(b[lo:hi]).hexdigest())
                     for lo,hi in ((0x2509,0x2584),(0xe000,0xeb00),(0xeb03,0xebe5),(0xef73,0xf070),(0xf073,0xf160))])
    manifest['generated']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in
            (ROOT/'core/source_audio_data.h',ROOT/'core/c64_sound_data.h',out/'waveforms.pcm',out/'source-registers.json')]
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Extracted15 source SFX; title{len(music)-loop}fields/loop; {len(bank)}Chip waveform bytes; {len(packets)}music packets')

if __name__=='__main__':build()
