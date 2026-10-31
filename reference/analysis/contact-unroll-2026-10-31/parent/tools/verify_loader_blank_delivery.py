"""Source-derived loader blanking; preserve prior delivery as historical proof."""
import hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/screen-corruption-2026-10-30'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def enabled():return 'static void blank_game_display(void){' in (ROOT/'amiga/main.c').read_text(encoding='utf-8-sig')
class FrozenView:
 def __init__(self,entries):self.files={e['path']:ROOT/BASE/'parent'/e['path'] for e in entries}
 def __fspath__(self):return os.fspath(ROOT)
 def __truediv__(self,p):return self.files.get(Path(p).as_posix(),ROOT/p)
def verify_parent():
 import verify_audio_boundary_delivery as parent
 import verify_compact_actor_delivery as compact
 manifest=read(BASE+'/parent/manifest.json')
 for e in manifest['files']:assert item(BASE+'/parent/'+e['path'])['sha256']==e['sha256'],e['path']
 saved=parent.ROOT;flag=getattr(compact,'_display_parent_replay',False)
 try:
  parent.ROOT=FrozenView(manifest['files']);compact._display_parent_replay=True
  result=parent.verify_current();assert result==read(BASE+'/parent/verified-report.json')
 finally:parent.ROOT=saved;compact._display_parent_replay=flag
 return result
def expected_main(old):
 pairs=[('static UBYTE game_field_active,game_field_busy,game_field_loading;','static UBYTE game_field_active,game_field_busy,game_field_loading;\nstatic void blank_game_display(void);'),
 ('static void source_game_load(long loading){','static void source_game_load(long loading){\n    if(loading)blank_game_display();'),
 ('static UWORD *copper[2];','''static UWORD *copper[2];
/* Source $09BC-$09C1 clears DEN before rebuilding a room. Keep both
 * lists blank until present_frame publishes a complete replacement. */
static void blank_game_display(void){
    copper[0][1]=copper[1][1]=0;
    hw->bplcon0=0;
}'''),
 ('    hw->cop1lc=(ULONG)list;','    list[1]=(game_field_active && game_field_loading)?0:0x4200;\n    hw->cop1lc=(ULONG)list;')]
 for before,after in pairs:assert old.count(before)==1;old=old.replace(before,after)
 return old
def verify_current():
 assert enabled();parent=verify_parent()
 old=(ROOT/BASE/'parent/amiga/main.c').read_text(encoding='utf-8-sig')
 assert (ROOT/'amiga/main.c').read_text(encoding='utf-8-sig')==expected_main(old)
 assert item('core/c64_rooms.c')['sha256']=='2d3692711dfd57cd2e108e697df2c01a958e47657e3d85069ee1930dec00efc1'
 assert item('core/c64_actor_programs.h')['sha256']=='a85c42da6af9e042fa903e9c1d6927144e50cce2ba3480edbe3ae13f78b53f2e'
 source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
 assert hashlib.sha256(source).hexdigest()==parent['source_sha256']
 assert source[0x9bc:0x9c4]==bytes.fromhex('ad11d029ef8d11d0')
 assert source[0x50db:0x50e6]==bytes.fromhex('ad11d0297f09108d11d060')
 paths=[BASE+'/parent/manifest.json',BASE+'/parent/verified-report.json','amiga/main.c','core/c64_rooms.c','core/c64_actor_programs.h',
  'tools/verify_loader_blank_delivery.py','tools/verify_compact_actor_delivery.py','tools/audit_native_loader_blank.py',
  'tools/inspect_corrupt_screen_snapshot.py','tools/capture_corrupt_screen_replay.py','tools/recover_loader_parent_contact_proof.py',BASE+'/snapshot.json',BASE+'/native-snapshot.json',BASE+'/loader-disassembly.txt','docs/LOADER_DISPLAY_BLANK.md']
 elf=item('amiga/out/bruce_amiga.elf')['sha256']
 snapshot=read(BASE+'/snapshot.json');assert snapshot['snapshot_unchanged'] and snapshot['room']==6
 assert item('.tmp/30.10.2026.uss')['sha256']==snapshot['snapshot_sha256']
 stored=read(BASE+'/native-snapshot.json');assert stored['text_matches_selected_elf'] and stored['text_bytes']==179044 and not stored['source_den'] and stored['source_display_control']=='0xb'
 paths += [BASE+'/source-memory.bin',BASE+'/copper-05bb7c.bpl',BASE+'/copper-065f7c.bpl',BASE+'/background.bpl']
 for label in ['native-blank','native-blank-r12']:
  p=BASE+'/'+label+'/report.json';r=read(p);assert r['status']=='passed_native_loader_blank_then_complete_publication' and r['normal_elf_sha256']==elf
  assert r['blank']['loading'] and not r['blank']['source_den'] and r['blank']['modes']==[0,0]
  assert not r['publication']['loading'] and r['publication']['source_den'] and not r['publication']['fault'] and r['background_pixel_errors']==0 and r['checked_pixels']==56320
  assert len(r['pause_stability_checks'])==3 and all(r['pause_stability_checks']) and len(r['pending_source_cells'])<=160
  for e in r['artifacts']:assert item(e['path'])['sha256']==e['sha256'];paths.append(e['path'])
  paths.append(p)
 p='reference/analysis/menu-publication-2026-10-29/loader-blank-menu/report.json';r=read(p)
 assert r['elf']['sha256']==elf and r['status']=='passed_scoped_native_menu_publication' and len(r['transitions'])>=10 and len(r['starts'])==2 and all(q['complete_front'] for q in r['samples'])
 paths.append(p);paths += [p.relative_to(ROOT).as_posix() for p in (ROOT/Path(p).parent).glob('*') if p.suffix in ['.bpl','.bin']]
 for mode in ['cli','adf']:
  p=BASE+'/normal-ui/'+mode+'/report.json';r=read(p);assert r['status']=='passed_current_normal_boot' and r['complete_menu'] and r['elf']['sha256']==elf
  for e in r['artifacts']:assert item(e['path'])['sha256']==e['sha256'];paths.append(e['path'])
  paths.append(p)
 for label in ['loader-blank-r12','loader-blank-r12-death']:
  p='reference/analysis/render-coherence-2026-10-29/'+label+'/report.json';r=read(p)
  assert r['elf']['sha256']==elf and r['snapshots_paused'] and len(r['samples'])>=12
  for k in ['mixed_phase_samples','max_pixel_mismatch','max_static_pixel_mismatch','max_flicker_illegal_pixels']:assert r[k]==0,k
  assert not r['flicker_stuck_codes'];paths.append(p)
  paths += [p.relative_to(ROOT).as_posix() for p in (ROOT/Path(p).parent).glob('*') if p.suffix in ['.bpl','.bin']]
 native=read('reference/validation/source-world-native.json');r=native['run']
 assert native['status']=='passed_scoped_native_source_contract' and r['source_actor_fixture_cases']=='53' and r['frames']=='1200' and r['restored_os']=='1'
 for k in ['source_actor_fixture_failure','c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','c64_render_mismatches','capture_fault','vic_compare_errors']:assert r[k]=='0',k
 assert int(r['chip_largest_loaded'])>=49152
 for e in native['source_files']:assert item(e['path'])['sha256']==e['sha256'],e['path']
 for e in native['build']:assert item(e['path'])['sha256']==e['sha256'];paths.append(e['path'])
 paths.append('reference/validation/source-world-native.json')
 p='reference/analysis/flat-control-compact-2026-10-30/delivery-kernels.json';links=read(p)
 assert links['status']=='passed_current_compact_primitive_linkage' and links['contact_kernels']==8
 for e in links['artifacts']:assert item(e['path'])['sha256']==e['sha256'];paths.append(e['path'])
 paths.append(p)
 from audit_vic_native_kernels import sections
 _,before=sections(ROOT/BASE/'parent/amiga/out/bruce_amiga.elf');_,after=sections(ROOT/'amiga/out/bruce_amiga.elf')
 sizes={k:(dict(after)[k][5]-dict(before)[k][5]) for k in ['.text','.rodata','.data','.bss']}
 assert 0<sizes['.text']<=256 and all(sizes[k]==0 for k in ['.rodata','.data','.bss'])
 extension=sorted((Path.home()/'.vscode/extensions').glob('bartmanabyss.amiga-debug-*'))[-1]
 objdump=extension/'bin/win32/opt/bin/m68k-amiga-elf-objdump.exe'
 for name in ['source_game_load','present_frame.isra.0']:
  asm=subprocess.check_output([str(objdump),'-d','--disassemble='+name,str(ROOT/'amiga/out/bruce_amiga.elf')],text=True)
  if name=='source_game_load':assert asm.count('clr.w 2(a0)')==2 and asm.index('clr.w 2(a0)')<asm.index('dff100')
  else:
   assert 'addi.w #-300,d0' in asm and 'cmpi.w #8,d0' in asm
   commit=asm.index('dff080');guard=asm.index('bhi.s');assert guard<commit and 'jsr' not in asm[guard:commit] and 'move.w d0,2(a0)' in asm[guard:commit]
  p=BASE+'/'+name.replace('.','-')+'-disassembly.txt';(ROOT/p).write_text(asm,encoding='utf-8');paths.append(p)
 outputs=['amiga/out/bruce_amiga.'+s for s in ['exe','elf','adf']]+['.tmp/amiga-boot/c/start']
 assert item(outputs[-1])['sha256']==item(outputs[0])['sha256']
 return dict(parent,status='scoped_complete_loader_display_blank_acceptance_open',largest_chip_block=int(r['chip_largest_loaded']),normal_build=[item(p) for p in outputs],
  loader_blank=dict(source_disable='$09BC-$09C1',source_enable='$0B33 -> $50DB-$50E5',normal_section_deltas=sizes,gameplay_core_unchanged=True,prior_host_engine_controls_reused_as_historical=True,fresh_native_controls=53,fresh_native_loops=1200),
  artifacts=[item(p) for p in sorted(set(paths))])
if __name__=='__main__':verify_current();print('PASS loader blank delivery; original real-time/original-edition gates remain open')
