"""Scope audit for the original R20 color stores; does not approve delivery/timing."""
import hashlib,json
from pathlib import Path
from verify_renderer_delta_scope import verify as renderer_scope, effective_source_path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/final-colors-2026-10-30'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def verify():
 derivation=renderer_scope()
 manifest=read(BASE+'/before/manifest.json')
 for e in manifest['files']:assert item(BASE+'/before/'+e['path'])['sha256']==e['sha256']
 modified={'core/c64_rooms.c','core/c64_actor_programs.h','tools/build_c64_rooms.py'}
 for e in manifest['files']:
  if e['path'].startswith(('core/','amiga/')) and Path(e['path']).suffix in ['.c','.h','.s'] and e['path'] not in modified:
   assert hashlib.sha256(effective_source_path(e['path']).read_bytes()).hexdigest()==e['sha256'],e['path']
 old=(ROOT/BASE/'before/core/c64_rooms.c').read_text();new=effective_source_path('core/c64_rooms.c').read_text(encoding='utf-8-sig')
 macro='''#if defined(__GNUC__)
#define SOURCE_INLINE static inline __attribute__((always_inline))
#else
#define SOURCE_INLINE static __forceinline
#endif
'''
 start=old.index('        unsigned short cell=address-0xd800;unsigned char color=m[address]&15;');end=old.index('    }else if(address>=0xa000',start);body=old[start:end]
 helper='''/* Color-only observer; all callers have already established index_ready and
 * the source $D878-$DBE7 range. Metadata effects match source_written. */
SOURCE_INLINE void source_color_written(unsigned short address){
'''+body+'}\n'
 loop='''/* Source $42A1-$42BA: eight stores per descending column, no IRQ/service
 * seam. The original DEX leaves X=$FF,N=1,Z=0; A/Y/C/V/D/SP are unchanged.
 * Entry guard in the generator retains the original path for X>$1C. */
static SOURCE_NOINLINE void source_final_colors(void){
    unsigned char column=x,row,value=a,ready=index_ready;
    do{
        unsigned short address=(unsigned short)(0xdaac+column);
        for(row=0;row<8;row++){
            m[address]=value;if(ready)source_color_written(address);
            address+=40;
        }
    }while(--column<128);
    x=column;z=0;n=1;
}
'''
 attr='''#if defined(__GNUC__)
#define SOURCE_NOINLINE __attribute__((noinline,noclone))
#else
#define SOURCE_NOINLINE __declspec(noinline)
#endif
'''
 astart=old.index('static void animation_cell_changed(unsigned short cell){');aend=old.index('static void rebuild_animation_fallback',astart);animation=old[astart:aend]
 active=animation.replace('static void animation_cell_changed(','''#if defined(__GNUC__)
__attribute__((noinline,noclone))
#else
__declspec(noinline)
#endif
static void animation_cell_changed_active(''').replace('    if(!animation_count)return;\n','')
 wrapper='''#if defined(__GNUC__)
static inline __attribute__((always_inline))
#else
static __forceinline
#endif
void animation_cell_changed(unsigned short cell){
    if(animation_count)animation_cell_changed_active(cell);
}
'''
 anchor='/* Native decoding of $17E2-$1817'
 expected=old.replace(animation,active+wrapper).replace(anchor,attr+helper+loop+anchor)
 assert new==expected,'Unexpected engine source changes outside guarded color stores/identical observer and explicit private animation guard'
 oldgen=(ROOT/BASE/'before/tools/build_c64_rooms.py').read_text();gen=(ROOT/'tools/build_c64_rooms.py').read_text()
 hook='''        if actors and pc==0x42a1:
            assert (op,mode,size,o)==('sta','abx',3,0xdaac)
            assert memory[0x42a1:0x42bc]==bytes.fromhex('9dacda9dd4da9dfcda9d24db9d4cdb9d74db9d9cdb9dc4dbca10e5')
            lines.append('if(x<=0x1c){source_final_colors();goto L42bc;}')
'''
 assert gen==oldgen.replace('        if pc==0x2cf1:lines.append',hook+'        if pc==0x2cf1:lines.append')
 oldheader=(ROOT/BASE/'before/core/c64_actor_programs.h').read_text();header=(ROOT/'core/c64_actor_programs.h').read_text();label='L42a1:; /* $42A1 */\n'
 assert header==oldheader.replace(label,label+'if(x<=0x1c){source_final_colors();goto L42bc;}\n')
 host=read(BASE+'/host.json');assert host['source_cases']==7424 and host['renderer_cases']==192 and host['source_instructions']==1113600 and host['full_ram_and_registers']
 for e in host['source_files']:assert hashlib.sha256(effective_source_path(e['path']).read_bytes()).hexdigest()==e['sha256'],e['path']
 return dict(status='passed_scoped_source_color_store_change',later_renderer_derivation=derivation,original_bytes_sha256=item('.reference/c64/work/untrained-memory.bin')['sha256'],changed_engine_sources=sorted(modified),unchanged_source_rules_outside_slice=True,extra_production_bss=0,source_cases=7424,renderer_cases=192,artifacts=[item(BASE+'/before/manifest.json'),item(BASE+'/host.json'),item(BASE+'/source-disassembly.txt'),item('tools/verify_renderer_delta_scope.py'),item('reference/analysis/color-observer-2026-10-30/source-scope.json')],limits=['Bounded source slice and old/new renderer metadata controls','Native controls, normal build, all-room timing and final acceptance remain separate'])
if __name__=='__main__':
 r=verify();(ROOT/BASE/'source-scope.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print('PASS original color-store scope; generic writer source unchanged; active animation body unchanged; remaining source rules unchanged')
