"""Decode inclusive/exclusive native PAL-line samples; never equate to C64 proof."""
import argparse,json,math
from pathlib import Path
NAMES=['loop','field','vic','game','room','contact','objects','combat','actors','sprites',
       'align','rows','sprite_copy','audio_source','audio_render','audio_dma','audio_publish',
       'view','background','restore','draw','load','wait',
       'contact_lanes','contact_classes','contact_swap']
def interval(i):
    if i<16:return [i,i]
    if i<31:return [16+(i-16)*16,31+(i-16)*16]
    if i<39:return [(i-30)*256,(i-29)*256-1]
    return [2304,None]
def main():
    p=argparse.ArgumentParser();p.add_argument('report',type=Path);a=p.parse_args()
    raw=dict(line.split('=',1) for line in a.report.read_text().splitlines() if '=' in line)
    slots=[]
    if raw.get('source_profile')=='1':
        assert raw['perf_errors']=='0'
        for i,name in enumerate(NAMES):
            calls,total,self_time,maximum,context,*bins=map(int,raw['perf_'+str(i)].split(','))
            assert len(bins)==40 and calls==sum(bins),(name,calls,sum(bins))
            assert self_time<=total
            quantiles={}
            for q in [50,95,99]:
                cumulative=0
                for j,count in enumerate(bins):
                    cumulative+=count
                    if calls and cumulative>=math.ceil(calls*q/100):quantiles['p'+str(q)+'_self_lines']=interval(j);break
            slots.append(dict(name=name,calls=calls,inclusive_lines=total,exclusive_lines=self_time,
                average_inclusive=round(total/calls,3) if calls else None,
                average_exclusive=round(self_time/calls,3) if calls else None,
                max_inclusive_lines=maximum,max_context=dict(room=(context>>24)+1,
                states=[(context>>16)&255,(context>>8)&255,context&255]),**quantiles))
    result=dict(method='Native PAL raster-line timer, nested samples; quantiles are histogram intervals',
        instrumentation_32_empty_pairs_lines=int(raw.get('perf_overhead_32_pairs_lines',0)),
        profile=slots,held_changed=int(raw['held_changed']),held_unchanged=int(raw['held_unchanged']),
        stage_loop=int(raw['stage_loop']),stage_valid=int(raw['stage_valid']),
        runtime_max_gap=int(raw['max_gap_excluding_framebuffer_capture']),
        audio_missed=int(raw['source_clock_missed']),source_steps=int(raw['source_world_steps']),
        realtime_accepted=False,natural_playthrough=False)
    a.report.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    for row in sorted(slots,key=lambda x:x['exclusive_lines'],reverse=True):
        print(f"{row['name']:16} calls={row['calls']:5} self={row['exclusive_lines']:8} mean={str(row['average_exclusive']):>8} max={row['max_inclusive_lines']:5}")
    print('held changed/unchanged:',result['held_changed'],result['held_unchanged'])
if __name__=='__main__':main()
