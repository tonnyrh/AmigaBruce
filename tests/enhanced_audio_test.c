/* Controlled source-queue -> Paula register/page tests. No source fixtures
 * or generated clips are overwritten by this executable. */
#include "../core/c64_rooms.c"
#include "../core/source_audio.h"
#include "../core/source_dma.h"
#include "../core/combat.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef unsigned char UBYTE;
typedef unsigned short UWORD;
typedef unsigned long ULONG;
#define DMAF_SETCLR 0x8000
#define DMAF_MASTER 0x0200
static struct {
    UWORD dmacon,intreq,intreqr;
    struct { volatile UWORD *ac_ptr; UWORD ac_len,ac_per,ac_vol; } aud[3];
} custom,*hw=&custom;
static UWORD chip_words[2+3*512+1];
static UBYTE *sfx_pcm=(UBYTE*)chip_words;
static BlPaulaVoice source_voices[3];
static BlSourceDma source_dma;
static ULONG line;
static ULONG line_clock(void){return ++line;}
unsigned long bl_source_audio_chip_bytes(void){return 4;}
static UBYTE *source_audio_images(void){return sfx_pcm+4;}
#include "../amiga/enhanced_audio.h"

static void jsr_sound(UWORD site,UBYTE actor,UBYTE fx){
    x=actor;y=fx;
    m[0x100+sp--]=(UBYTE)((site+2)>>8);m[0x100+sp--]=(UBYTE)(site+2);
    source_sound();
}
static void request(UWORD ch,UBYTE fx,UBYTE actor,UWORD site){
    /* Force earlier C64 queues busy, so $2509 selects ch. */
    m[0xeb00]=(ch>0);m[0xef70]=(ch>1);m[0xf070]=0;
    m[0x51]=actor;jsr_sound(site,actor,fx);
}
static UWORD tick(UWORD *restart){
    UWORD c;
    for(c=0;c<3;c++){source_voices[c].period=450;source_voices[c].volume=40;}
    *restart=0;return foley_tick(restart);
}
static void finisher_case(UBYTE attacker,UBYTE victim,UBYTE hp,UBYTE state,UBYTE latch,UBYTE expected){
    static UBYTE seed[65536],baseline[65536];
    UBYTE before_regs[13]={0},after_regs[13]={0};
    UWORD i,restart;
    BlCombat world={0};
    bl_c64_reset();bl_c64_actor_seed();bl_c64_actor_test_call(0x0f72,0);
    bl_c64_load(0);bl_c64_actor_test_call(0x0b30,0);
    for(i=0;i<5;i++)m[0x4f40+i]=(UBYTE)(i/2);
    for(i=0;i<3;i++){
        m[0x95+i]=(UBYTE)(i==0?1:i==1?0x81:0x41);
        m[0x106+i]=m[0x4fdb+i]=0;m[0x4f45+i]=2;
        m[0x9e+i]=150;m[0xa1+i]=40;m[0xa4+i]=1;
        m[0xbf+i]=m[0xce+i]=0;m[0xd1+i]=36;
    }
    m[0xd01e]=latch;m[0x88]=m[0x40]=0;
    m[0x9e+attacker]=60;m[0xa1+attacker]=150;m[0xbf+attacker]=state;m[0xce+attacker]=7;
    m[0x9e+victim]=68;m[0xa1+victim]=150;m[0xd1+victim]=hp;
    memcpy(seed,m,65536);
    bl_c64_set_finisher_observer(0);bl_c64_set_sound_observer(0);
    bl_c64_actor_test_call(0x29c3,0);assert(!source_fault);
    memcpy(baseline,m,65536);bl_c64_actor_registers(before_regs);
    memcpy(m,seed,65536);foley_begin();
    bl_c64_actor_test_call(0x29c3,0);assert(!source_fault);
    bl_c64_actor_registers(after_regs);
    assert(!memcmp(m,baseline,65536) && !memcmp(before_regs,after_regs,13));
    assert(foley_finisher_pending==expected);
    foley_actions(&world,1);
    if(expected){
        UWORD channel=3,id=2*FX_BRUCE_FINISH;
        for(i=0;i<3;i++)if(foley_voice[i].pending==FOLEY_FIRST_CUE+FX_BRUCE_FINISH)channel=i;
        assert(channel<3 && !foley_finisher_pending && (m[0xd1+victim]&128));
        tick(&restart);line+=1000;tick(&restart);
        assert(hw->aud[channel].ac_len==500 && hw->aud[channel].ac_per==foley_samples[id].period);
        for(i=0;i<500;i++)assert(chip_words[2+channel*512+i]==foley_expand[foley_bank[foley_samples[id].offset+i]]);
        assert(foley_played_mask&(1UL<<id));
        foley_actions(&world,1);
        for(i=0;i<3;i++)assert(foley_voice[i].pending!=FOLEY_FIRST_CUE+FX_BRUCE_FINISH);
        request(channel,0x8e,0,0); /* A footstep must not cut the cry short. */
        tick(&restart);assert(!restart && foley_voice[channel].mode==FOLEY_PCM);
        assert(foley_voice[channel].pending==FOLEY_RESTORE);
        hw->intreqr=(UWORD)(0x80u<<channel);tick(&restart);
        assert(foley_voice[channel].armed==1 && !restart);
        tick(&restart);assert(foley_voice[channel].armed==2 && !restart);
        hw->intreqr=0;tick(&restart);line+=1000;tick(&restart);
        assert(restart==(1u<<channel) && foley_voice[channel].mode==FOLEY_SID);
    }
    foley_end();assert(!finisher_observer);
}
int main(void){
    static const UBYTE actors[]={0,0,1,1,2,2,2,1};
    static const UWORD sites[]={0x227c,0x205a,0x227c,0x209f,0x227c,0x209f,0x22d2,0x2e30};
    static const UBYTE effects[]={0x85,0x84,0x85,0x84,0x85,0x84,0x85,0x86};
    UWORD cue,v,ch,restart,mask,i;
    bl_c64_reset();foley_begin();chip_words[2+3*512]=0x5aa5;
    for(cue=0;cue<8;cue++)for(v=0;v<2;v++){
        UWORD id=2*cue+v;ch=(cue+v)%3;
        UWORD *page=chip_words+2+ch*512;
        request(ch,effects[cue],actors[cue],sites[cue]);
        assert(foley_voice[ch].pending==FOLEY_FIRST_CUE+cue);
        mask=tick(&restart);
        assert(mask==(1u<<ch) && !restart && !hw->aud[ch].ac_vol);
        line+=1000;mask=tick(&restart);
        assert(mask==(1u<<ch) && !restart && hw->aud[ch].ac_ptr==page);
        assert(hw->aud[ch].ac_len==foley_samples[id].words && hw->aud[ch].ac_per==foley_samples[id].period);
        assert(hw->aud[ch].ac_vol==foley_samples[id].volume && !source_voices[ch].volume);
        for(i=0;i<hw->aud[ch].ac_len;i++)assert(page[i]==foley_expand[foley_bank[foley_samples[id].offset+i]]);
        hw->intreqr=(UWORD)(0x80u<<ch);tick(&restart);
        assert(hw->aud[ch].ac_ptr==chip_words && hw->aud[ch].ac_len==2);
        hw->intreqr=0;request(ch,0x8e,0,0);
        mask=tick(&restart);
        assert(!mask && restart==(1u<<ch) && source_dma.offset[ch]==65535);
        assert(hw->aud[ch].ac_ptr==page && hw->aud[ch].ac_len==512);
    }
    assert(foley_played_mask==65535 && chip_words[2+3*512]==0x5aa5);
    request(0,0x85,0,0x227c);request(1,0x84,1,0x205a);request(2,0x85,2,0x22d2);
    assert(tick(&restart)==7);line+=1000;assert(tick(&restart)==7);
    assert(hw->aud[0].ac_per==foley_samples[0].period && hw->aud[2].ac_per==foley_samples[12].period);
    /* $2509 may clobber X while choosing a busy voice by priority. */
    m[0xeb00]=m[0xef70]=m[0xf070]=1;
    m[0x2581]=m[0x2582]=255;m[0x2583]=0;
    jsr_sound(0x2a93,1,0x87);assert(foley_voice[2].pending==FOLEY_FIRST_CUE+FX_YAMO_HIT);
    m[0x2583]=255;jsr_sound(0x227c,0,0x85);assert(foley_voice[2].pending==FOLEY_FIRST_CUE+FX_YAMO_HIT);
    request(0,0x8c,1,0x3059);assert(foley_voice[0].pending==FOLEY_FIRST_CUE+FX_YAMO_HIT);
    request(0,0x8c,0,0x3059);assert(foley_voice[0].pending==FOLEY_RESTORE);
    foley_end();assert(!foley_active && !sound_observer);
    {
        BlCombat world={0};
        foley_begin();m[0xeb00]=m[0xef70]=m[0xf070]=0;
        world.player.active=1;world.player.body.source_state=17;world.player.body.source_counter=4;
        foley_actions(&world,1);assert(foley_voice[2].pending==FOLEY_FIRST_CUE+FX_BRUCE_PUNCH);
        assert(!m[0xeb00] && !m[0xef70] && !m[0xf070]);
        foley_voice[2].pending=0;world.player.body.source_counter=3;foley_actions(&world,1);
        assert(!foley_voice[2].pending);
        world.player.body.source_counter=4;foley_actions(&world,1);
        assert(foley_voice[2].pending==FOLEY_FIRST_CUE+FX_BRUCE_PUNCH);
        request(0,0x84,0,0x205a);world.player.body.source_state=12;foley_actions(&world,1);
        assert(foley_voice[0].pending==FOLEY_FIRST_CUE+FX_BRUCE_KICK && !foley_voice[1].pending);
        foley_end();
    }
    for(i=1;i<3;i++){
        UBYTE latch=(UBYTE)(i==1?15:51);
        for(v=0;v<5;v++)finisher_case(0,(UBYTE)i,(UBYTE)v,17,latch,(UBYTE)(v<3));
        finisher_case(0,(UBYTE)i,2,12,latch,0); /* A lethal kick is not a punch. */
        finisher_case(0,(UBYTE)i,2,17,0,0); /* A missed punch cannot finish. */
    }
    finisher_case(1,2,2,17,60,0); /* Yamo kills Kage: no Bruce cry. */
    finisher_case(1,0,2,17,15,0); /* Bruce is the victim. */
    {
        BlCombat world={0};
        foley_begin();
        m[0xeb00]=m[0xef70]=m[0xf070]=1;
        for(i=0;i<3;i++)foley_voice[i].pending=FOLEY_FIRST_CUE+FX_YAMO_KICK;
        foley_finisher(1);foley_actions(&world,1);
        assert(foley_voice[2].pending==FOLEY_FIRST_CUE+FX_BRUCE_FINISH);
        foley_voice[2].pending=0;foley_finisher(2);foley_actions(&world,0);
        assert(!foley_finisher_pending && !foley_voice[2].pending); /* No stale room event. */
        foley_end();
    }
    puts("PASS 17 unique samples, queue routing, 16 source combat cases, exact RAM/register preservation, finisher one-shot and busy/room guards");
    return 0;
}
