/* Isolated native candidate for the original game raster IRQ handlers.
 * Explicit pin values and caller PC; no physical raster-timing assertion.
 * Includes every source stack store. No opcode interpreter is used here. */
#include "input_slot.h"
static void irq_context_push(unsigned char value){m[0x100+sp--]=value;}
static unsigned char irq_context_pop(void){return m[0x100+(unsigned char)++sp];}
static void irq_context_frame(unsigned short ret){irq_context_push((unsigned char)(ret>>8));irq_context_push((unsigned char)ret);}
static unsigned short irq_context_rts(void){unsigned short ret=irq_context_pop();ret|=(unsigned short)irq_context_pop()<<8;return (unsigned short)(ret+1);}
static void irq_context_status(unsigned char status){c=status&1;z=(status>>1)&1;actor_i=(status>>2)&1;d=(status>>3)&1;v=(status>>6)&1;n=status>>7;}
static unsigned char irq_context_read(unsigned char zp){return m[(unsigned short)(W(zp)+y)];}
static void irq_context_frequency(unsigned short queue,unsigned short sid,unsigned char zp){
    ++y;NZ(y);a=irq_context_read(zp);NZ(a);m[queue+2]=a;
    ++y;NZ(y);a=irq_context_read(zp);x=a;NZ(x);
    a=m[0xe200+x];NZ(a);m[sid]=a;
    a=m[0xe254+x];NZ(a);m[sid+1]=a;++y;NZ(y);
    (void)irq_context_rts();
}
static void irq_context_gate(unsigned short sid,unsigned char zp){
    a=irq_context_read(zp);NZ(a);audio_write((unsigned short)(sid+4),a);++y;NZ(y);
    (void)irq_context_rts();
}
static unsigned short irq_context_voice(unsigned short queue,unsigned short sid,unsigned char zp,unsigned short delta){
    unsigned char command;
    a=m[queue];NZ(a);if(!z){
        if(n){
            c=a>>7;a=(unsigned char)(a<<1);x=a;NZ(x);
            a=m[0xebe5+x];NZ(a);m[zp]=a;
            a=m[0xebe6+x];NZ(a);m[(unsigned char)(zp+1)]=a;
            y=1;NZ(y);m[queue+2]=m[queue]=y;
            --y;NZ(y);audio_write((unsigned short)(sid+4),y);m[queue+1]=y;
        }
        --m[queue+2];NZ(m[queue+2]);
        if(z){
            y=m[queue+1];NZ(y);a=irq_context_read(zp);x=a;NZ(x);command=x;
            a=m[0xec03+x];NZ(a);m[(unsigned short)(0xeb39+delta)]=a;c=0;
            if(command>7 || a!=(unsigned char)(command*3)){source_fault=0xee01;return 0;}
            if(!command){
                a=0;NZ(a);m[sid]=m[sid+1]=m[queue]=m[queue+1]=a;
            }else{
                if(command==7){++y;NZ(y);irq_context_frame((unsigned short)(0xebe0+delta));irq_context_gate(sid,zp);}
                else{
                    unsigned short ret=command==1?0xeba4:command==2?0xebab:command==3?0xebb5:command==4?0xebc2:0xebd2;
                    irq_context_frame((unsigned short)(ret+delta));irq_context_frequency(queue,sid,zp);
                    if(command==3 || command==4){
                        irq_context_frame((unsigned short)((command==3?0xebb8:0xebc5)+delta));
                        a=irq_context_read(zp);x=a;NZ(x);
                        a=m[0xec11+x];NZ(a);m[sid+5]=a;
                        a=m[0xec12+x];NZ(a);m[sid+6]=a;++y;NZ(y);(void)irq_context_rts();
                    }
                    if(command>=4){
                        irq_context_frame((unsigned short)((command==4?0xebc8:0xebd5)+delta));
                        a=irq_context_read(zp);NZ(a);++y;NZ(y);x=a;NZ(x);
                        a=m[0xec1b+x];NZ(a);m[sid+2]=a;
                        a=m[0xec1c+x];NZ(a);m[sid+3]=a;(void)irq_context_rts();
                    }
                    if(command!=1){
                        ret=command==2?0xebae:command==3?0xebbb:command==4?0xebcb:0xebd8;
                        irq_context_frame((unsigned short)(ret+delta));irq_context_gate(sid,zp);
                    }
                }
                m[queue+1]=y;
            }
        }
    }
    return irq_context_rts();
}
static void irq_context_next_band(void){
    m[0xd01a]=m[0xd019]=1;m[0xd011]&=127;
    m[0xd012]=m[(unsigned short)(0x47f5+m[0x44])];
    if(m[0xd012]==253){m[0x408]=0xc1;m[0x409]=0x48;}
}
static unsigned short irq_context_candidate(unsigned short pc,unsigned char port0,unsigned char port1){
    unsigned char status;unsigned short handler,ret;
    if(actor_i)return pc;
    irq_context_frame(pc);
    status=(unsigned char)(0x20|c|(z<<1)|(d<<3)|(v<<6)|(n<<7));irq_context_push(status);actor_i=1;
    irq_context_push(a);irq_context_push(x);irq_context_push(y);
    x=sp;NZ(x);a=(unsigned char)(m[(unsigned short)(0x104+x)]&m[0x110d]);NZ(a);
    handler=W(0x408);
    if(handler==0x48c1){
        m[0xd018]=0x32;m[0xd021]=0xfc;m[0x408]=0x1e;m[0x409]=0x49;
        m[0xd01a]=m[0xd019]=1;m[0xd011]&=127;m[0xd012]=0x40;
        a=m[0x29];c=a>>7;a=(unsigned char)(a<<1);x=a;NZ(x);
        m[0x0a]=m[0x480b+x];m[0x0b]=m[0x480c+x];m[0x0c]=m[0x4833+x];m[0x0d]=m[0x4834+x];
        y=11;
        do{
            a=m[(unsigned short)(W(0x0a)+y)];m[0x153+y]=a;
            c=y>=4;
            if(!c){a=m[(unsigned short)(W(0x0c)+y)];m[0x47f5+y]=a;}
            --y;NZ(y);
        }while(!n);
        irq_context_frame(0x4917);d=0;a=0;NZ(a);m[0x44]=a;x=m[0x29];NZ(x);
        irq_context_frame(0x15b1);ret=irq_context_voice(0xeb00,0xd400,0xf6,0);if(ret!=0x15b2)return 0;
        irq_context_frame(0x15b4);ret=irq_context_voice(0xef70,0xd407,0xf8,0x470);if(ret!=0x15b5)return 0;
        irq_context_frame(0x15b7);ret=irq_context_voice(0xf070,0xd40e,0xfa,0x570);if(ret!=0x15b8)return 0;
        actor_irq_stop=0;actor_code(0x15b8);actor_irq_stop=0;
        input_slot_candidate(port0,port1);
        actor_code(0x1703);actor_irq_stop=0;
        ret=irq_context_rts();if(ret!=0x4918){source_fault=0xee02;return ret;}
    }else if(handler==0x491e){
        m[0xd018]=m[0xf2];m[0xd021]=m[0x153];m[0xd022]=m[0x154];m[0xd023]=m[0x155];
        m[0x44]=0;m[0xf4]=3;m[0x408]=0x82;m[0x409]=0x49;irq_context_next_band();
    }else if(handler==0x4982){
        m[0xd021]=m[0x153+m[0xf4]];m[0xd022]=m[0x154+m[0xf4]];m[0xd023]=m[0x155+m[0xf4]];
        a=m[0xf4];c=0;adc(3);m[0xf4]=a;++m[0x44];irq_context_next_band();
    }else if(handler==0x14a4){
        static const unsigned char colors[7]={0xfb,0xfc,0xff,0xf1,0xff,0xfc,0xfb};
        static const unsigned char delays[7]={2,2,2,1,2,2,0};
        static const unsigned short returns[11]={0x14be,0x14c1,0x14c9,0x14cc,0x14d4,0x14d7,0x14df,0x14e7,0x14ea,0x14f2,0x14f5};
        unsigned char group,call=0,count;
        /* $1526 contains only LDX/DEX/BNE/RTS: retain ordered source
         * color/frame writes while excluding physical beam/CPU delays. */
        for(group=0;group<7;group++){
            m[0xd022]=colors[group];
            for(count=0;count<delays[group];count++){
                irq_context_frame(returns[call++]);(void)irq_context_rts();
            }
        }
        m[0xd018]=0x30;m[0xd016]=0x18;m[0xd01a]=m[0xd019]=1;m[0xd011]&=127;m[0xd012]=0x63;
        if(m[0x48])--m[0x48];
    }else if(handler==0x1574){
        m[0xd018]=0x32;m[0xd016]=0x16;m[0x408]=0x2c;m[0x409]=0x15;
        m[0xd01a]=m[0xd019]=1;m[0xd011]&=127;m[0xd012]=0xfd;
    }else{source_fault=0xee03;return pc;}
    y=irq_context_pop();x=irq_context_pop();a=irq_context_pop();
    irq_context_status(irq_context_pop());ret=irq_context_pop();ret|=(unsigned short)irq_context_pop()<<8;
    return ret;
}
