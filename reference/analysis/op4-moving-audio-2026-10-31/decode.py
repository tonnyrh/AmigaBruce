"""Read both windows around every missed Paula service; units are PAL raster lines."""
import json
from pathlib import Path
import struct
import sys
SCOPES="other sound game_field irq_prefix irq_input_tail vic world_step contact objects combat actors sprites prepare_paint load_background patch_background restore animate projectiles fighters health lives score present".split()
SITES="start game_entry post_field before_input post_step post_prepare before_draw blitter capture_scan presentation_wait bitmap_clear prepare_target".split()
ORIGINS="outer contact_row contact_driver legacy_contact legacy_tick source_sprite translated_contact".split()
def report(path):
    return dict(line.split("=",1) for line in path.read_text().splitlines() if "=" in line)
def decode(folder):
    r=report(folder/"op0-light.txt");raw=(folder/"op4-audio.bin").read_bytes()
    values=list(x[0] for x in struct.iter_unpack(">I",raw))
    magic,timed,n,width,count,ticks,lost,polls=values[:8]
    assert magic==0x4f503401 and timed in (0,1) and n==len(SCOPES) and width==14+2*n
    assert count<=32 and len(values)==8+count*width
    assert (ticks,lost)==(int(r["audio_ticks"]),int(r["audio_missed"]))
    assert abs(ticks+lost-int(r["pal_fields"]))<=1 and polls>=ticks
    events=[]
    for at in range(8,len(values),width):
        row=values[at:at+width];step,field,gap,prev,porig,pgap,pphase,last,lorig,lphase,site,orig,pmask,tmask=row[:14]
        assert step<240 and gap>1 and pmask & ~tmask==0
        e=dict(step=step,field=field,gap=gap,missed=gap-1,previous_poll=SITES[prev]+"/"+ORIGINS[porig],
               previous_gap=pgap,previous_phase=pphase,last_tick=SITES[last]+"/"+ORIGINS[lorig],
               last_tick_phase=lphase,late_poll=SITES[site]+"/"+ORIGINS[orig])
        for w,(name,mask) in enumerate((("previous_poll",pmask),("last_tick",tmask))):
            lines=row[14+w*n:14+(w+1)*n]
            assert all(mask&(1<<i) or v==0 for i,v in enumerate(lines))
            e[name+"_work"]={k:(lines[i] if timed else None) for i,k in enumerate(SCOPES) if mask&(1<<i)}
            if timed:e[name+"_lines"]=sum(lines)
        if timed:assert e["previous_poll_lines"]<=e["last_tick_lines"]
        events.append(e)
    assert sum(e["missed"] for e in events)==lost
    return dict(pal_fields=int(r["pal_fields"]),missed=lost,polls=polls,timed=bool(timed),events=events)
if __name__=="__main__":
    print(json.dumps(decode(Path(sys.argv[1])),indent=2))
