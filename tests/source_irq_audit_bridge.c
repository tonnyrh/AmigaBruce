/* Read-only host audit seam; production code is included without edits. */
#include "../core/c64_rooms.c"
void bl_irq_audit_prepare(long human){bl_c64_reset();bl_c64_world_start(1,human);}
void bl_irq_audit_seed(const unsigned char *ram,const unsigned char *r,long input,long other){
 unsigned long i;for(i=0;i<65536;i++)m[i]=ram[i];
 a=r[0];x=r[1];y=r[2];c=r[3];z=r[4];n=r[5];v=r[6];d=r[7];sp=r[8];actor_i=r[9];
 loaded=m[0x29];actor_world_enabled=1;actor_preparing=actor_irq_stop=actor_delay_pending=actor_gameover_pending=actor_reset_pending=0;
 actor_return=0;actor_stop_pc=0x1c32;source_fault=0;transition_pending=0;index_ready=0;io_service=0;
 vic_valid=vic_collision_valid=0;actor_input=(unsigned char)input;actor_yamo_input=(unsigned char)other;
}
void bl_irq_audit_field(long audio){unsigned char registers[26];if(audio)bl_c64_audio_frame(registers);bl_c64_field();}
void bl_irq_audit_copy(unsigned char *out){unsigned long i;for(i=0;i<65536;i++)out[i]=m[i];}
void bl_irq_audit_regs(unsigned char *out){out[0]=a;out[1]=x;out[2]=y;out[3]=c;out[4]=z;out[5]=n;out[6]=v;out[7]=d;out[8]=sp;out[9]=actor_i;}
void bl_irq_audit_inputs(unsigned char *out){out[0]=m[0x98];out[1]=m[0x9b];out[2]=m[0x99];out[3]=m[0x9c];}
