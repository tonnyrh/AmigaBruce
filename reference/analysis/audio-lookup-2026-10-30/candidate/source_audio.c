#include "source_audio.h"
#include "source_audio_data.h"
static unsigned short faults;
unsigned long bl_source_audio_chip_bytes(void){return BL_SOURCE_AUDIO_CHIP_BYTES;}
void bl_source_audio_copy(unsigned char *chip){unsigned short i;for(i=0;i<BL_SOURCE_AUDIO_CHIP_BYTES;i++)chip[i]=bl_source_wave_bytes[i];}
void bl_source_audio_reset(BlSourceAudio *s){unsigned short i;unsigned char *p=(unsigned char*)s;for(i=0;i<sizeof(*s);i++)p[i]=0;faults=0;}
unsigned short bl_source_audio_faults(void){return faults;}
void bl_source_audio_music(BlSourceAudio *s,unsigned char *out){
    unsigned char i;
    if(!s->music_wait){
        unsigned long mask;unsigned short at=s->music_cursor;
        if(at>=BL_SOURCE_MUSIC_BYTES)at=BL_SOURCE_MUSIC_LOOP;
        s->music_wait=bl_source_music[at++];s->music_regs[25]=bl_source_music[at++];
        mask=bl_source_music[at]|((unsigned long)bl_source_music[at+1]<<8)|
            ((unsigned long)bl_source_music[at+2]<<16)|((unsigned long)bl_source_music[at+3]<<24);at+=4;
        for(i=0;i<25;i++,mask>>=1)if(mask&1)s->music_regs[i]=bl_source_music[at++];
        s->music_cursor=at;
    }
    --s->music_wait;for(i=0;i<26;i++)out[i]=s->music_regs[i];
}
void bl_source_audio_render(BlSourceAudio *s,const unsigned char *r,BlPaulaVoice *out){
    unsigned char v;
    for(v=0;v<3;v++){
        const unsigned char *p=r+v*7;BlPaulaVoice *o=out+v;
        unsigned short fn=(unsigned short)(p[0]|((unsigned short)p[1]<<8)),pw=(unsigned short)((p[2]|((unsigned short)p[3]<<8))&4095);
        unsigned char wave=p[4]&240,gate=p[4]&1;unsigned long step,target;
        unsigned short low=0,high=BL_SOURCE_FREQUENCIES,length=8,match;
        if((r[25]&(1<<v)) || (gate&&!s->gate[v]))s->phase[v]=0;
        if(!gate)s->phase[v]=3;
        s->gate[v]=gate;
        if(s->phase[v]==0){
            step=bl_source_attack_step[p[5]>>4];
            if(step>=65535-s->level[v]){s->level[v]=65535;s->phase[v]=1;}
            else s->level[v]+=step;
        }else if(s->phase[v]==1){
            target=(unsigned long)(p[6]>>4)*4369UL;step=bl_source_release_step[p[5]&15];
            if(s->level[v]<=target || step>=s->level[v]-target){s->level[v]=target;s->phase[v]=2;}
            else s->level[v]-=step;
        }else if(s->phase[v]==3){
            step=bl_source_release_step[p[6]&15];s->level[v]=s->level[v]>step?s->level[v]-step:0;
        }
        o->offset=BL_SOURCE_AUDIO_CHIP_BYTES-4;o->length=4;o->period=400;o->volume=0;
        if(!fn||!wave||(p[4]&8))continue;
        while(low<high){unsigned short mid=(unsigned short)((low+high)/2);
            if(bl_source_frequencies[mid][0]<fn)low=(unsigned short)(mid+1);else high=mid;}
        if(low>=BL_SOURCE_FREQUENCIES||bl_source_frequencies[low][0]!=fn){++faults;continue;}
        o->period=bl_source_frequencies[low][wave==128?3:1];length=bl_source_frequencies[low][2];
        if(wave==128){o->offset=BL_SOURCE_NOISE_OFFSET;o->length=BL_SOURCE_NOISE_BYTES;}
        else{
            if(wave==16||wave==32)pw=0;
            /* Generated keys are sorted by waveform, pulse width, length.
             * Find the same exact key without scanning all preceding waves. */
            low=0;high=BL_SOURCE_WAVES;
            while(low<high){
                unsigned short mid=(unsigned short)((low+high)/2);
                const unsigned short *key=bl_source_waves[mid];
                if(key[0]<wave || (key[0]==wave &&
                   (key[1]<pw || (key[1]==pw && key[2]<length))))low=(unsigned short)(mid+1);
                else high=mid;
            }
            match=low;
            if(match>=BL_SOURCE_WAVES || bl_source_waves[match][0]!=wave ||
               bl_source_waves[match][1]!=pw || bl_source_waves[match][2]!=length){++faults;continue;}
            o->offset=bl_source_waves[match][3];o->length=length;
        }
        /* Q16 envelope to0..64 volume, then source master volume0..15.
         * Envelope is an explicit50Hz approximation, not SID ADSR emulation. */
        o->volume=(unsigned short)((s->level[v]+512)>>10);
        o->volume=(unsigned short)((o->volume*(r[24]&15)+7)/15);
        if(v==2 && (r[24]&128) && !(r[23]&4))o->volume=0;
    }
}
