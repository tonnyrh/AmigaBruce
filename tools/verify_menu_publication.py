"""Check immutable baseline, actual menu bitmaps and unchanged game-loop source."""
import argparse,hashlib,json,re
from pathlib import Path
from verify_renderer_delta_scope import effective_source_path
from audit_native_menu_publication import reference
from audit_vic_native_kernels import sections
from rip_c64_room_graphics import render
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/menu-publication-2026-10-29'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def verify():
 paths=[BASE+'/before/manifest.json',BASE+'/menu-paint-disassembly.txt','tools/verify_menu_publication.py','tools/audit_native_menu_publication.py','docs/MENU_PUBLICATION.md']
 before=read(paths[0]);unchanged=[];later=[]
 from verify_final_color_scope import verify as color_scope
 assert read('reference/analysis/final-colors-2026-10-30/source-scope.json')==color_scope()
 paths += ['reference/analysis/final-colors-2026-10-30/source-scope.json','tools/verify_final_color_scope.py']
 for entry in before['files']:
  assert item(BASE+'/before/'+entry['path'])['sha256']==entry['sha256']
  if entry['path'].startswith(('core/','amiga/')) and Path(entry['path']).suffix in ['.c','.h','.s'] and entry['path']!='amiga/main.c':
   if item(entry['path'])==entry:unchanged.append(entry)
   else:
    assert entry['path'] in ['core/c64_rooms.c','core/c64_actor_programs.h']
    assert item('reference/analysis/final-colors-2026-10-30/before/'+entry['path'])['sha256']==entry['sha256']
    later.append(item(entry['path']))
 old=(ROOT/BASE/'before/amiga/main.c').read_text(encoding='utf-8');new=effective_source_path('amiga/main.c').read_text(encoding='utf-8-sig');marker='    source_audio_start(0);'
 assert old[old.index(marker):]==new[new.index(marker):],'In-game loop source changed'
 path=BASE+'/observer-final/report.json';r=read(path);paths.append(path)
 assert r['status']=='passed_scoped_native_menu_publication' and r['snapshots_paused'] and not r['natural_playthrough']
 assert item('amiga/out/bruce_amiga.elf')['sha256']==r['elf']['sha256']
 for entry in r['source_files']:assert item(entry['path'])==entry
 assert len(r['samples'])>=50 and len(r['transitions'])>=10
 conf=dict(debug=False,players=1,human=False,infinite=False,invincible=False,room=0);allowed={};known={reference(),reference(loading=True)}
 for index,t in enumerate(r['transitions']):
  previous=reference(**conf);conf=t['config'];current=reference(**conf);assert hashlib.sha256(current).hexdigest()==t['expected_sha256']
  allowed['change%02d'%index]={previous,current};known.add(current)
 partial=changed=f10_work=f10_changed=0;previous=None;held_game=None
 for index,row in enumerate(r['samples']):
  files=[BASE+'/observer-final/sample%03d-%s.bpl'%(index,name) for name in ['front','hidden']];paths+=files
  front,hidden=[(ROOT/p).read_bytes() for p in files];assert len(front)==len(hidden)==40960
  assert hashlib.sha256(front).hexdigest()==row['front_sha256'] and hashlib.sha256(hidden).hexdigest()==row['hidden_sha256']
  assert row['complete_front']
  if row['label']!='game-start':
   if row['label']=='f10-return':permitted=(known-{reference(loading=True)})|{held_game}
   else:permitted=allowed[row['label'].split('-')[0]] if row['label'].startswith('change') else known
   if row['label']=='f10-return' and front==held_game and hidden not in permitted:
    f10_work+=1
    if previous and previous['label']=='f10-return' and previous['hidden_sha256']!=row['hidden_sha256']:f10_changed+=1
   assert front in permitted,(index,row['label'])
   if row['hidden_not_a_complete_transition_image']:
    assert hidden not in permitted;partial+=1
    if previous and previous['front_index']==row['front_index'] and previous['hidden_sha256']!=row['hidden_sha256']:changed+=1
  else:
   assert front not in known;held_game=front
  previous=row
 assert partial==r['partial_hidden_samples'] and changed==r['changed_partial_hidden_samples'] and changed>0
 for entry in r['ram_states']:assert item(entry['path'])==entry;paths.append(entry['path'])
 assert r['ram_states'][0]['sha256']==r['ram_states'][1]['sha256'] and r['source_ram_preserved_during_choices']
 assert [x['menu_front'] for x in r['starts']]==[1,0] and all(x['source_fault']==0 for x in r['starts'])
 assert f10_work>0 and f10_changed>0
 # The held room image is an actual source-glyph comparison, excluding
 # source actor rectangles and designated animated glyphs, not guessed geometry.
 first_game=next(i for i,row in enumerate(r['samples']) if row['label']=='game-start')
 bitmap=(ROOT/(BASE+'/observer-final/sample%03d-front.bpl'%first_game)).read_bytes()
 ram=(ROOT/r['ram_states'][2]['path']).read_bytes();expected=render(ram,ram[0x29]);skip=[]
 for actor in range(3):
  if ram[0x95+actor]&1:
   x=ram[0x9e+actor]*2-24;y=ram[0xa1+actor];skip.append((x-20,y-30,x+40,y+10))
 checked=errors=0
 for y in range(24,200):
  for x in range(320):
   if any(l<=x<rr and top<=y<bottom for l,top,rr,bottom in skip):continue
   if 0x61<=ram[0x8c00+(y//8)*40+x//8]&127<=0x63:continue
   value=sum(1<<plane for plane in range(4) if bitmap[(y+32)*160+plane*40+x//8]&(128>>(x&7)))
   errors+=value!=expected.getpixel((x,y));checked+=1
 assert checked>=30000 and errors==0

 footprint=[]
 for p in [BASE+'/before/amiga/out/bruce_amiga.elf','amiga/out/bruce_amiga.elf']:
  _,ss=sections(ROOT/p);footprint.append(dict(build=item(p),sections={name:s[5] for name,s in ss if name in ['.text','.data','.rodata','.bss']}))
 assert footprint[0]['sections']['.bss']==footprint[1]['sections']['.bss']
 return dict(status='passed_menu_publication_and_start_buffers',edition_verified=False,natural_playthrough=False,realtime_accepted=False,samples=len(r['samples']),partial_hidden_samples=partial,changed_partial_hidden_samples=changed,f10_partial_hidden_samples=f10_work,f10_changed_hidden_samples=f10_changed,held_room_checked_pixels=checked,held_room_static_pixel_errors=errors,source_ram_preserved=True,game_start_fronts=[1,0],unchanged_engine_files=unchanged,later_scoped_engine_sources=later,footprint=footprint,artifacts=[item(p) for p in paths],limits=['Paused controlled UI snapshots, not whole-game or timing acceptance','Menu choices and source-start calls retained; no new C64 rule','Background start copies use existing blocking OCS blit; no clean startup timing claim yet'])
def main():
 p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();r=verify();path=ROOT/'reference/validation/menu-publication.json'
 if a.record:path.write_text(json.dumps(r,indent=2)+'\n')
 else:assert read(path)==r
 print('PASS menu publication:',r['samples'],'frames;',r['changed_partial_hidden_samples'],'changing hidden samples; both start fronts')
if __name__=='__main__':main()
