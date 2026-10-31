"""Generate an isolated $25E2 native candidate; never edit production code."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/sprite-publish-2026-10-30'
def main():
    base=BASE/'candidate';base.mkdir(parents=True,exist_ok=True)
    core=(ROOT/'core/c64_rooms.c').read_text(encoding='utf-8-sig')
    anchor='#include "c64_actor_programs.h"';assert core.count(anchor)==1
    core=core.replace(anchor,'#include "publish.h"\n'+anchor)
    (base/'c64_rooms.c').write_text(core,encoding='utf-8')
    program=(ROOT/'core/c64_actor_programs.h').read_text(encoding='utf-8-sig')
    label='L25e2:; /* $25E2 */\n';assert program.count(label)==1
    program=program.replace(label,label+'if(!d && !m[0x277e]){source_sprite_publish();actor_return=source_stack_return();return;}\n')
    (base/'c64_actor_programs.h').write_text(program,encoding='utf-8')
    bridge=(ROOT/'tests/source_contact_bridge.c').read_text(encoding='utf-8-sig')
    bridge=bridge.replace('#include "../core/c64_rooms.c"','#include "candidate/c64_rooms.c"')
    (BASE/'bridge.c').write_text(bridge,encoding='utf-8')
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    (BASE/'scope.json').write_text(json.dumps(dict(status='isolated_native_sprite_publish_candidate',production_changed=False,inputs=[item(ROOT/p) for p in ['core/c64_rooms.c','core/c64_actor_programs.h','tests/source_contact_bridge.c']],generated=[item(base/p) for p in ['c64_rooms.c','c64_actor_programs.h','publish.h']]+[item(BASE/'bridge.c')],source_entry='$25E2',source_last='$269F',guard='Binary arithmetic and original $277E zero guard; all other entries keep original generated code'),indent=2)+'\n',encoding='utf-8')
    print('Generated isolated native sprite-publish candidate; production unchanged')
if __name__=='__main__':main()
