"""Pack only tour diagnostics; validate before narrowing every recorded value.

Production source, allocations and game state are not changed. Fixed source
step/room outputs remain backed by runtime equality checks, not assumptions.
"""
import argparse,hashlib,json
from pathlib import Path
def main():
    p=argparse.ArgumentParser();p.add_argument('--path',type=Path,required=True);a=p.parse_args()
    text=a.path.read_text(encoding='utf-8-sig');before=hashlib.sha256(text.encode()).hexdigest()
    def replace(old,new):
        nonlocal text
        assert text.count(old)==1,old
        text=text.replace(old,new)
    replace('typedef struct {ULONG steps,fields,lines,missed,drawn,held,preparation,actual_room,chip_largest,slow_largest,animation_bytes;} BlTourSample;',
            'typedef struct {ULONG lines,preparation,chip_largest,slow_largest,animation_bytes;UWORD fields,missed,drawn,held;} BlTourSample;')
    replace('''                        sample->steps=steps;sample->fields=(field_clock()-perf_tour_base_field)&0xffffffUL;
                        sample->lines=(line_clock()-perf_tour_base_line)&0xffffffUL;sample->missed=source_clock_missed-perf_tour_base_missed;
                        sample->drawn=drawn_images-perf_tour_base_drawn;sample->held=held_images-perf_tour_base_held;
                        sample->actual_room=1+bl_c64_read(0x29);++perf_tour_completed;perf_tour_active=0;''',
'''                        ULONG fields=(field_clock()-perf_tour_base_field)&0xffffffUL;
                        ULONG lines=(line_clock()-perf_tour_base_line)&0xffffffUL;
                        ULONG missed=source_clock_missed-perf_tour_base_missed;
                        ULONG drawn=drawn_images-perf_tour_base_drawn,held=held_images-perf_tour_base_held;
                        if((fields|missed|drawn|held)&0xffff0000UL){perf_tour_error=5;PERF_END(BL_PERF_LOOP);break;}
                        if(bl_c64_read(0x29)!=perf_tour_room){perf_tour_error=6;PERF_END(BL_PERF_LOOP);break;}
                        sample->fields=(UWORD)fields;sample->lines=lines;sample->missed=(UWORD)missed;
                        sample->drawn=(UWORD)drawn;sample->held=(UWORD)held;
                        ++perf_tour_completed;perf_tour_active=0;''')
    replace('number(&p,sample->steps);','number(&p,120);')
    replace('number(&p,sample->actual_room);','number(&p,tour+1);')
    assert "if(steps!=120){perf_tour_error=2;" in text
    a.path.write_text(text,encoding='utf-8')
    meta_path=a.path.with_suffix('.json');meta=json.loads(meta_path.read_text(encoding='utf-8-sig'))
    meta.update(unmodified_generated_sha256=meta['generated_sha256'],pre_compact_sha256=before,
        generated_sha256=hashlib.sha256(text.encode()).hexdigest(),diagnostic_compact_stats=True,
        stats_record_bytes_before=44,stats_record_bytes_after=28,stats_bss_saved=320,
        guarded_narrowing=['fields','missed','drawn','held'],validated_fixed_outputs=['steps=120','actual_room=sample_index+1'],
        overflow_error=5,room_mismatch_error=6,production_source_edited=False,unused_capture_allocation_omitted=True)
    meta_path.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    print('Packed only tour statistics: 320 BSS bytes saved; explicit overflow and source room/step checks')
if __name__=='__main__':main()
