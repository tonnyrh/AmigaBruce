#include "irq_context.h"
unsigned long owner_vector(void){return W(0x408);}
unsigned long owner_line(void){return (unsigned long)m[0xd012]+((m[0xd011]&128)?256UL:0UL);}
static unsigned char owner_pin(unsigned char input){
    return (unsigned char)(source_direction(input)|((input&BL_FIRE)?0:16));
}
/* Split raw execution from the existing field-sampled VIC seam so the
 * complete IRQ state can also be independently checked against source. */
static unsigned short owner_irq(unsigned short pc,unsigned char p0,unsigned char p1){
    unsigned short saved_return=actor_return,saved_stop=actor_stop_pc;
    unsigned char saved_irq_stop=actor_irq_stop;
    unsigned short ret=irq_context_candidate(pc,p0,p1);
    actor_return=saved_return;actor_stop_pc=saved_stop;actor_irq_stop=saved_irq_stop;
    return ret;
}
unsigned long owner_dispatch(unsigned long pc,unsigned char *registers){
    unsigned short vector=W(0x408),ret;
    unsigned char i,p0=owner_pin(actor_yamo_input),p1=owner_pin(actor_input);
    if(!pc || actor_i || (vector!=0x48c1 && vector!=0x491e && vector!=0x4982))return 0;
    if(m[3]){unsigned char t=p0;p0=p1;p1=t;}
    if(vector==0x48c1)audio_gates=0;
    ret=owner_irq((unsigned short)pc,p0,p1);
    if(source_fault || ret!=pc)return 0;
    if(vector==0x48c1){
        for(i=0;i<25;i++)registers[i]=m[0xd400+i];
        registers[25]=audio_gates;
        source_vic_latch();
    }
    return vector;
}
