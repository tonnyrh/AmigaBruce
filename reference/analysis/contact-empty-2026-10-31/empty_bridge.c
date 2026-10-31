/* Host-only entry seam; actual source bytes are executed separately. */
#include "C:/vscode/_EXT/AmigaBruceLee/core/c64_rooms.c"
static unsigned char service_trace[64][10];static unsigned short service_count;
static void contact_trace(void){
    unsigned char *r=service_trace[service_count++];
    r[0]=a;r[1]=x;r[2]=y;r[3]=c;r[4]=z;r[5]=n;r[6]=v;r[7]=d;r[8]=sp;r[9]=actor_i;
}
void bl_contact_trace_enable(void){service_count=0;actor_world_enabled=1;io_service=contact_trace;}
long bl_contact_trace(unsigned char *out){unsigned short i;for(i=0;i<service_count*10;i++)out[i]=((unsigned char*)service_trace)[i];return service_count;}
void bl_contact_seed(const unsigned char *ram,const unsigned char *r){
    unsigned long at;for(at=0;at<65536;at++)m[at]=ram[at];
    a=r[0];x=r[1];y=r[2];c=r[3];z=r[4];n=r[5];v=r[6];d=r[7];sp=r[8];actor_i=r[9];
    actor_world_enabled=actor_preparing=actor_irq_stop=actor_delay_pending=actor_gameover_pending=actor_reset_pending=0;
    actor_stop_pc=actor_return=source_fault=0;transition_pending=0;io_service=0;
}
void bl_contact_run(long entry){actor_code((unsigned short)entry);}
void bl_contact_copy(unsigned char *out){unsigned long at;for(at=0;at<65536;at++)out[at]=m[at];}
void bl_contact_regs(unsigned char *r){
    r[0]=a;r[1]=x;r[2]=y;r[3]=c;r[4]=z;r[5]=n;r[6]=v;r[7]=d;r[8]=sp;r[9]=actor_i;
}
unsigned long bl_contact_return(void){return actor_return;}
unsigned long bl_contact_fault(void){return source_fault;}

__declspec(dllexport) void bl_empty_host_run(long body){if(body)source_contact_body_c();else source_contact_classes_c();}
