"""Put test-only 20-room statistics in an explicit 880-byte Chip allocation.

All source metrics retain 32 bits. Collection boundaries, game buffers and
production source remain unchanged. Before/after tests use the same layout.
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
    replace('static BlTourSample perf_tour_samples[20];',
        'typedef char TourSampleSizeCheck[(sizeof(BlTourSample)==44)?1:-1];\nstatic BlTourSample *perf_tour_samples;')
    anchor='    if(BL_AUTOTEST)arithmetic_errors=bruce_runtime_check();'
    replace(anchor,anchor+'''
    perf_tour_samples=AllocMem(sizeof(BlTourSample)*20,MEMF_CHIP|MEMF_CLEAR);
    if(!perf_tour_samples){result=20;goto cleanup;}''')
    anchor='cleanup:\n'
    replace(anchor,anchor+'    if(perf_tour_samples)FreeMem(perf_tour_samples,sizeof(BlTourSample)*20);\n')
    anchor='''        append(&p,"\\nsource_tour_completed=");number(&p,perf_tour_completed);'''
    replace(anchor,'''
        append(&p,"\\nsource_tour_stats_bytes=");number(&p,sizeof(BlTourSample)*20);
        append(&p,"\\nsource_tour_stats_address=");number(&p,(ULONG)perf_tour_samples);
        append(&p,"\\nsource_tour_stats_memory=");number(&p,TypeOfMem(perf_tour_samples));
'''+anchor)
    a.path.write_text(text,encoding='utf-8')
    meta_path=a.path.with_suffix('.json');meta=json.loads(meta_path.read_text(encoding='utf-8-sig'))
    meta.update(unmodified_generated_sha256=meta['generated_sha256'],pre_heap_stats_sha256=before,
        generated_sha256=hashlib.sha256(text.encode()).hexdigest(),diagnostic_heap_stats=True,
        stats_record_bytes=44,stats_allocation_bytes=880,stats_net_bss_saved=876,
        stats_allocation='MEMF_CHIP|MEMF_CLEAR; freed in cleanup; actual memory type/address included in report',
        production_source_edited=False,unused_capture_allocation_omitted=True,
        limits=['Diagnostic Chip allocation counts against unchanged 49152-byte reserve','All source values remain 32-bit; no narrowed counters or assumed fixed outputs'])
    meta_path.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    print('Moved only full-width tour statistics to explicit 880-byte Chip allocation; net BSS -876 bytes')
if __name__=='__main__':main()
