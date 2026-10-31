/* Candidate-only, explicitly parameterized source IRQ context. */
#include "candidate/c64_rooms.c"
#include "../irq-input-2026-10-30/candidate/irq_context.h"
static unsigned short irq_candidate_pc;
void bl_irq_context_prepare(long room,long human){bl_c64_reset();bl_c64_world_start(1,human);if(room)bl_c64_world_jump(room);}
void bl_irq_context_seed(const unsigned char *ram,const unsigned char *r){
    unsigned long i;for(i=0;i<65536;i++)m[i]=ram[i];
    a=r[0];x=r[1];y=r[2];c=r[3];z=r[4];n=r[5];v=r[6];d=r[7];sp=r[8];actor_i=r[9];
    loaded=m[0x29];actor_world_enabled=1;actor_preparing=actor_irq_stop=actor_delay_pending=actor_gameover_pending=actor_reset_pending=0;
    actor_return=0;actor_stop_pc=0x1c32;source_fault=0;transition_pending=0;index_ready=0;io_service=0;audio_gates=0;
    vic_valid=vic_collision_valid=0;
}
void bl_irq_context_run(long pc,long port0,long port1){irq_candidate_pc=irq_context_candidate((unsigned short)pc,(unsigned char)port0,(unsigned char)port1);}
void bl_irq_context_copy(unsigned char *out){unsigned long i;for(i=0;i<65536;i++)out[i]=m[i];}
void bl_irq_context_regs(unsigned char *out){out[0]=a;out[1]=x;out[2]=y;out[3]=c;out[4]=z;out[5]=n;out[6]=v;out[7]=d;out[8]=sp;out[9]=actor_i;}
long bl_irq_context_pc(void){return irq_candidate_pc;}
long bl_irq_context_fault(void){return source_fault;}
long bl_irq_context_gates(void){return audio_gates;}
