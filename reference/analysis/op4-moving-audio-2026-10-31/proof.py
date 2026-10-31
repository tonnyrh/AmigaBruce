from probe import HERE,ROOT,WORK,compile_program
import shutil
def build():
    f=WORK/"proof";f.mkdir(exist_ok=True)
    base=HERE.parent/"irq-input-2026-10-30/candidate"
    for name in ("irq_context.h","input_slot.h"):shutil.copyfile(base/name,f/name)
    core=(ROOT/"core/c64_rooms.c").read_text()+'''
#include "irq_context.h"
unsigned char *pilot_ram(void){return m;}
unsigned long pilot_witness(unsigned char *r,unsigned char *wanted,unsigned char *unused){
    unsigned long at;unsigned short returned;unsigned char after[10];(void)unused;
    a=r[0];x=r[1];y=r[2];c=r[3];z=r[4];n=r[5];v=r[6];d=r[7];sp=r[8];actor_i=r[9];
    loaded=m[0x29];actor_world_enabled=1;actor_preparing=actor_irq_stop=actor_delay_pending=actor_gameover_pending=actor_reset_pending=0;
    actor_return=0;actor_stop_pc=0x1c32;source_fault=0;transition_pending=0;index_ready=0;io_service=0;
    audio_gates=0;vic_valid=vic_collision_valid=0;
    returned=irq_context_candidate(0x2c51,r[10],r[11]);
    if(source_fault || returned!=0x2c51 || audio_gates!=r[12])return 1;
    after[0]=a;after[1]=x;after[2]=y;after[3]=c;after[4]=z;after[5]=n;after[6]=v;after[7]=d;after[8]=sp;after[9]=actor_i;
    for(at=0;at<10;at++)if(after[at]!=r[at])return 2;
    for(at=0;at<65536UL;at++)if(m[at]!=wanted[at])return at+3;
    return 0;
}
'''
    main=(HERE.parent/"op1-kage-prefix-2026-10-31/proof_main.c").read_text()
    main=main.replace("header[35]","header[13]").replace("Read(input,header,35)!=35","Read(input,header,13)!=13")
    main=main.replace("last=AllocMem(65536UL,MEMF_PUBLIC);","").replace(" || !last","").replace(" || Read(input,last,65536)!=65536","")
    (f/"main.c").write_text(main);(f/"c64_rooms.c").write_text(core)
    compile_program(f,ROOT/".tmp/op1-kage/reference")
if __name__=="__main__":build()
