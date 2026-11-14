/* Native decoding of $EB03/$EF73/$F073. Uses the room module's shadow m[].
 * Source tables/data are extracted separately; no6502 interpreter. */
#include "c64_sound_data.h"
static unsigned char audio_gates;
static unsigned short audio_faults;
static unsigned char audio_data(unsigned short at){
    if(at>=0xebe5 && at<0xef70)return bl_source_sfx_data[at-0xebe5];
    ++audio_faults;return 0;
}
static void audio_write(unsigned short address,unsigned char value){
    if((address==0xd404||address==0xd40b||address==0xd412) && (value&1) && !(m[address]&1))
        audio_gates|=(unsigned char)(1<<((address-0xd404)/7));
    m[address]=value;
}
static void audio_driver(unsigned short queue,unsigned short sid,unsigned char zp,unsigned short branch){
    unsigned char index,position,command,parameter;unsigned short pointer;
    if(!m[queue])return;
    if(m[queue]&128){
        index=(unsigned char)(m[queue]<<1);
        m[zp]=audio_data((unsigned short)(0xebe5+index));m[zp+1]=audio_data((unsigned short)(0xebe6+index));
        m[queue+2]=m[queue]=1;audio_write(sid+4,0);m[queue+1]=0;
    }
    if(--m[queue+2])return;
    pointer=(unsigned short)(m[zp]|((unsigned short)m[zp+1]<<8));position=m[queue+1];
    command=audio_data((unsigned short)(pointer+position));
    if(command>7){++audio_faults;m[queue]=0;return;}
    m[branch]=audio_data((unsigned short)(0xec03+command));
    if(!command){m[sid]=m[sid+1]=m[queue]=m[queue+1]=0;return;}
    if(command==7){++position;audio_write(sid+4,audio_data((unsigned short)(pointer+position)));++position;m[queue+1]=position;return;}
    ++position;m[queue+2]=audio_data((unsigned short)(pointer+position));++position;
    index=audio_data((unsigned short)(pointer+position));++position;
    if(index>=86){++audio_faults;m[queue]=0;return;}
    m[sid]=bl_source_sfx_freq_lo[index];m[sid+1]=bl_source_sfx_freq_hi[index];
    if(command==3||command==4){
        parameter=audio_data((unsigned short)(pointer+position));++position;
        m[sid+5]=audio_data((unsigned short)(0xec11+parameter));m[sid+6]=audio_data((unsigned short)(0xec12+parameter));
    }
    if(command>=4){
        parameter=audio_data((unsigned short)(pointer+position));++position;
        m[sid+2]=audio_data((unsigned short)(0xec1b+parameter));m[sid+3]=audio_data((unsigned short)(0xec1c+parameter));
    }
    if(command!=1){audio_write(sid+4,audio_data((unsigned short)(pointer+position)));++position;}
    m[queue+1]=position;
}
void bl_c64_audio_reset(void){
    unsigned char i;m[0xeb00]=m[0xef70]=m[0xf070]=0;
    for(i=0;i<=32;i++)m[0xd400+i]=0;
    audio_gates=0;
}
void bl_c64_audio_request(long effect){
    unsigned char saved[9]={a,x,y,c,z,n,v,d,sp};
    if(effect<128||effect>142){++audio_faults;return;}
    y=(unsigned char)effect;source_queue_sound(0);
    a=saved[0];x=saved[1];y=saved[2];c=saved[3];z=saved[4];n=saved[5];v=saved[6];d=saved[7];sp=saved[8];
}
void bl_c64_audio_frame(unsigned char *registers){
    unsigned char i;audio_gates=0;
    audio_driver(0xeb00,0xd400,0xf6,0xeb39);
    audio_driver(0xef70,0xd407,0xf8,0xefa9);
    audio_driver(0xf070,0xd40e,0xfa,0xf0a9);
    for(i=0;i<25;i++)registers[i]=m[0xd400+i];
    registers[25]=audio_gates;
}
unsigned short bl_c64_audio_faults(void){return audio_faults;}
unsigned short bl_c64_audio_requests(void){return audio_requests_mask;}
