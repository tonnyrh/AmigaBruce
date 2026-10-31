/* Explicit candidate seam; does not replace production source_actor_field. */
#include "../core/c64_rooms.c"
#include "../reference/analysis/irq-input-2026-10-30/candidate/input_slot.h"
void bl_input_slot_seed(const unsigned char *ram,const unsigned char *r){
    unsigned long i;for(i=0;i<65536;i++)m[i]=ram[i];
    a=r[0];x=r[1];y=r[2];c=r[3];z=r[4];n=r[5];v=r[6];d=r[7];sp=r[8];actor_i=r[9];
}
void bl_input_slot_run(long port0,long port1){input_slot_candidate((unsigned char)port0,(unsigned char)port1);}
void bl_input_slot_copy(unsigned char *out){unsigned long i;for(i=0;i<65536;i++)out[i]=m[i];}
void bl_input_slot_regs(unsigned char *out){out[0]=a;out[1]=x;out[2]=y;out[3]=c;out[4]=z;out[5]=n;out[6]=v;out[7]=d;out[8]=sp;out[9]=actor_i;}
