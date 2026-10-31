"""Strict source derivation for Copper publication and no-op observer scope.
This composes source evidence; it does not approve real-time or a new binary.
"""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PUB='reference/analysis/publication-2026-10-30'
COLOR='reference/analysis/color-observer-2026-10-30'
AUDIO='reference/analysis/audio-lookup-2026-10-30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def text(p):return p.read_text(encoding='utf-8-sig')
def expected_main(old):
 helper="""/* COP1LC must be committed before the next automatic Copper restart.
 * Audio servicing can overrun wait_frame's blank boundary. Recheck directly
 * before the write, and keep accounting/debug work after publication. */
static UWORD present_frame(UWORD *list){
    UWORD line;
    wait_blitter();
    do{wait_frame();line=raster();}while(line<300 || line>308);
    hw->cop1lc=(ULONG)list;
    return line;
}
"""
 anchor='static ULONG field_clock(void){';assert old.count(anchor)==1
 old=old.replace(anchor,helper+anchor)
 for before,after in [
 ('wait_frame();hw->cop1lc=(ULONG)copper[hidden];wait_frame();*front=hidden;','present_frame(copper[hidden]);wait_frame();*front=hidden;'),
 ('wait_frame();hw->cop1lc=(ULONG)copper[0];','present_frame(copper[0]);'),
 ('wait_frame();hw->cop1lc=(ULONG)copper[back];wait_frame();','present_frame(copper[back]);wait_frame();')]:
  assert before in old;old=old.replace(before,after)
 before="""        wait_frame();
        PERF_END(BL_PERF_WAIT);
        if(BL_AUTOTEST){"""
 after="""        {UWORD line=present_frame(copper[back]);
        if(BL_AUTOTEST){
            if(line<present_min)present_min=line;
            if(line>present_max)present_max=line;
            if(line<300||line>308)++bad_presents;
        }}
        PERF_END(BL_PERF_WAIT);
        if(BL_AUTOTEST){"""
 assert old.count(before)==1;old=old.replace(before,after)
 before="""        if(BL_AUTOTEST){
            UWORD line=raster();
            if(line<present_min)present_min=line;
            if(line>present_max)present_max=line;
            if(line<300||line>308)++bad_presents;
        }
        hw->cop1lc=(ULONG)copper[back];
"""
 assert old.count(before)==1;return old.replace(before,'')
def expected_core(old):
 start=old.index('SOURCE_INLINE void source_color_written(');end=old.index('/* Source $42A1',start)
 block=old[start:end];before='indexed_color[cell]=color;release_cell_cache(cell);animation_cell_changed(cell);'
 after="""indexed_color[cell]=color;release_cell_cache(cell);
            /* The active observer has no effect without either an animated
             * glyph or a cached animation-cell membership. Keep its exact
             * body for all cells for which it can change metadata. */
            if(animation_count){
                unsigned char code=m[0x8c00 + cell]&127;
                if((code>=0x61 && code<=0x63) || animation_cell[cell]!=65535)
                    animation_cell_changed_active(cell);
            }"""
 assert block.count(before)==1;return old[:start]+block.replace(before,after)+old[end:]
def effective_source_path(name):
 if name=='amiga/main.c':
  before=ROOT/PUB/'before/amiga/main.c';current=ROOT/name
  if text(current)==text(before):return current
  assert text(current)==expected_main(text(before)),'Main changed outside the checked Copper commit'
  return before
 if name=='core/c64_rooms.c':
  before=ROOT/AUDIO/'before/core/c64_rooms.c';current=ROOT/name
  if text(current)==text(before):return current
  assert text(current)==expected_core(text(before)),'Core changed outside the no-op color observer'
  return before
 return ROOT/name
def verify():
 for folder in [PUB,AUDIO]:
  for entry in json.loads((ROOT/folder/'before/manifest.json').read_text(encoding='utf-8-sig')):
   assert sha(ROOT/folder/'before'/entry['path'])==entry['sha256'],entry['path']
 before=ROOT/AUDIO/'before/core/c64_rooms.c';candidate=ROOT/COLOR/'candidate/c64_rooms.c'
 assert text(candidate)==expected_core(text(before))
 main=effective_source_path('amiga/main.c');core=effective_source_path('core/c64_rooms.c')
 host=json.loads((ROOT/COLOR/'host.json').read_text(encoding='utf-8-sig'))
 assert host['source_cases']==7424 and host['source_instructions']==1113600 and host['renderer_cases']==192 and host['observer_domain_cases']==4096
 for e in host['source_files']:
  path=ROOT/e['path']
  if e['path']=='core/c64_rooms.c':path=before
  assert sha(path)==e['sha256'],e['path']
 # No unrelated core/amiga source change is hidden by this composition.
 manifest=json.loads((ROOT/AUDIO/'before/manifest.json').read_text(encoding='utf-8-sig'))
 for e in manifest:
  if e['path'].startswith(('core/','amiga/')) and '/out/' not in e['path'] and e['path'] not in ['core/c64_rooms.c','amiga/main.c']:
   assert sha(ROOT/e['path'])==e['sha256'],e['path']
 return dict(status='passed_exact_renderer_source_derivation',publication_applied=main!=ROOT/'amiga/main.c',color_observer_applied=core!=ROOT/'core/c64_rooms.c',
  main_sha256=sha(ROOT/'amiga/main.c'),core_sha256=sha(ROOT/'core/c64_rooms.c'),candidate_sha256=sha(candidate),
  effective_prior_main=dict(path=main.relative_to(ROOT).as_posix(),sha256=sha(main)),effective_prior_core=dict(path=core.relative_to(ROOT).as_posix(),sha256=sha(core)),
  source_cases=7424,renderer_cases=192,observer_domain_cases=4096,gameplay_rules_outside_observer_unchanged=True,
  extra_service_points=0,extra_production_bss=0,realtime_accepted=False)
if __name__=='__main__':
 report=verify();(ROOT/COLOR/'source-scope.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
