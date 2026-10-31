"""Reproduce the private direct-call variant from the frozen V1 candidate."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/sprite-publish-2026-10-30'
def main():
 target=BASE/'direct-call';target.mkdir(exist_ok=True)
 for name in ['c64_rooms.c','c64_actor_programs.h','publish.h']:
  text=(BASE/'candidate'/name).read_text(encoding='utf-8-sig')
  if name=='c64_actor_programs.h':
   old='m[0x100 + sp--]=0x15;m[0x100 + sp--]=0xbc;actor_code(0x25e2);'
   new='m[0x100 + sp--]=0x15;m[0x100 + sp--]=0xbc;if(!d){source_sprite_publish();actor_return=source_stack_return();}else actor_code(0x25e2);'
   assert text.count(old)==1;text=text.replace(old,new)
  (target/name).write_text(text,encoding='utf-8')
 bridge=(ROOT/'tests/source_contact_bridge.c').read_text(encoding='utf-8-sig')
 bridge+='\nvoid bl_contact_prepare(long room,long human){bl_c64_reset();bl_c64_world_start(1,human);if(room)bl_c64_world_jump(room);}\n'
 (target/'bridge-before.c').write_text(bridge.replace('#include "../core/c64_rooms.c"','#include "../../../../core/c64_rooms.c"'),encoding='utf-8')
 (target/'bridge.c').write_text(bridge.replace('#include "../core/c64_rooms.c"','#include "c64_rooms.c"'),encoding='utf-8')
 def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 (target/'scope.json').write_text(json.dumps(dict(status='isolated_direct_call_experiment',production_changed=False,derivation='V1 publisher unchanged; only source JSR $15BA uses a direct binary-mode call; original two stack stores, return decoding, decimal fallback and all continuation guards retained',inputs=[item(BASE/'candidate'/n) for n in ['c64_rooms.c','c64_actor_programs.h','publish.h']],generated=[item(target/n) for n in ['c64_rooms.c','c64_actor_programs.h','publish.h','bridge.c','bridge-before.c']]),indent=2)+'\n')
 print('Generated private direct-call variant; production unchanged')
if __name__=='__main__':main()
