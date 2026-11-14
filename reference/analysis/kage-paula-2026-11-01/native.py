"""Run the same original-byte cases and both planar score drawers on 68000."""
import importlib.util
import sys
import struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("kage_pilot",HERE/"build.py")
pilot=importlib.util.module_from_spec(spec);spec.loader.exec_module(pilot)
ROOT,WORK=pilot.ROOT,pilot.WORK
out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else WORK/"proof"
engine=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else WORK/"fold"
core=(engine/"c64_rooms.c").read_text()
actor=(engine/"c64_actor_programs.h").read_text()
actor=pilot.insert(actor,0x2c1d,"if(stop_at_damage){actor_return=0x2c1d;return;}")
core="static unsigned char stop_at_damage;\n"+core+'''
unsigned char *proof_ram(void){return m;}
unsigned long proof_kage(const unsigned char *r,const unsigned char *expected){
    unsigned long i;
    stop_at_damage=*r++;actor_world_enabled=1;actor_invincible=!stop_at_damage;
    a=r[0];x=r[1];y=r[2];c=r[3];z=r[4];n=r[5];v=r[6];d=r[7];sp=r[8];actor_i=r[9];
    actor_return=actor_stop_pc=source_fault=0;transition_pending=0;
    actor_code(stop_at_damage?0x2bf9:0x29c3);
    if(source_fault || actor_return!=(stop_at_damage?0x2c1d:0x1c26))return 1;
    r+=10;
    if(a!=r[0] || x!=r[1] || y!=r[2] || c!=r[3] || z!=r[4] || n!=r[5] || v!=r[6] ||
       d!=r[7] || sp!=r[8] || actor_i!=r[9])return 2;
    for(i=0;i<65536UL;i++)if(m[i]!=expected[i])return 3+i;
    return 0;
}
'''
main=(WORK/"hud/main.c").read_text().replace("int main(void) {","int unused_route(void) {")
old=(ROOT/".tmp/op-pipeline/candidate/main.c").read_text()
start=old.index("static void draw_score(");end=old.index("\n}",start)+2
main+=old[start:end].replace("draw_score(","original_score(")+(HERE/"native_main.c").read_text().replace("count!=124","count!="+str(struct.unpack(">I",(out/"cases.bin").open("rb").read(4))[0]))
for name,code in (("main.c",main),("c64_rooms.c",core),("c64_actor_programs.h",actor),("source_audio.h",(WORK/"hud/source_audio.h").read_text())):(out/name).write_text(code)
pilot.compile_program(out,ROOT/".tmp/op-pipeline/candidate")
