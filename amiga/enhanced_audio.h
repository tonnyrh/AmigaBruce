/* Enhanced PCM borrows only the Paula voice assigned by the source queue.
 * The 1024-byte page belongs to that voice in both playback modes. */
#include "enhanced_audio_data.h"
enum { FOLEY_SID, FOLEY_STOPPED, FOLEY_PCM };
enum { FOLEY_NO_REQUEST, FOLEY_RESTORE, FOLEY_FIRST_CUE };
typedef struct {
    UBYTE mode,pending,next,armed;
    UWORD period,guard;
    ULONG stopped;
} FoleyVoice;
static FoleyVoice foley_voice[3];
static UBYTE foley_active,foley_variant[FX_COUNT],foley_finisher_pending;
static UBYTE foley_last_action[3],foley_last_counter[3],foley_announced;
static ULONG foley_played_mask;

static void foley_finisher(long victim){
    if(victim==1 || victim==2)foley_finisher_pending=1;
}

static UBYTE foley_finisher_playing(const FoleyVoice *voice){
    return voice->next==FOLEY_FIRST_CUE+FX_BRUCE_FINISH &&
        (voice->mode==FOLEY_STOPPED || (voice->mode==FOLEY_PCM && voice->armed<2));
}

static void foley_request(long channel,long effect,long actor,long site){
    UBYTE request=FOLEY_RESTORE;
    /* Let the 250 ms cry finish; resume the live source wave afterwards.
     * Source queues keep running and no old swing is replayed late. */
    if(foley_finisher_playing(&foley_voice[channel])){
        foley_voice[channel].pending=FOLEY_RESTORE;return;
    }
    if(actor<3){
        /* $205A/$209F (kick), $227C (punch), $22D2 (Kage thrust). */
        if(effect==0x84 && (site==0x205a || site==0x209f))request=FOLEY_FIRST_CUE+actor*2+1;
        else if(effect==0x85 && site==0x227c)request=FOLEY_FIRST_CUE+actor*2;
        else if(effect==0x85 && actor==2 && site==0x22d2)request=FOLEY_FIRST_CUE+FX_KAGE_BLADE;
        /* X is the victim at $2E30/$2A93. $3059 uses saved victim $51. */
        else if(actor==1 && ((effect==0x86 && site==0x2e30) || (effect==0x87 && site==0x2a93) ||
                             (effect==0x8c && site==0x3059)))
            request=FOLEY_FIRST_CUE+FX_YAMO_HIT;
    }
    if(request>=FOLEY_FIRST_CUE && request!=FOLEY_FIRST_CUE+FX_YAMO_HIT)
        foley_announced|=(UBYTE)(1u<<actor);
    foley_voice[channel].pending=request;
}

static void foley_actions(const BlCombat *world,UBYTE same_room){
    /* A normal player punch can enter state 17 with only four ticks.
     * $2274 sounds it only at eight. Give such short swings a free voice
     * without writing a request into the original priority queues. */
    static const UWORD queue[3]={0xeb00,0xef70,0xf070};
    UWORD actor;
    for(actor=0;actor<3;actor++){
        const BlFighter *fighter=actor?&world->enemy[actor-1]:&world->player;
        UBYTE state=fighter->body.source_state,timer=fighter->body.source_counter,action=0;
        if(fighter->active){
            if(state==17)action=FOLEY_FIRST_CUE+actor*2;
            else if(state==12 || state==13)action=FOLEY_FIRST_CUE+actor*2+1;
            else if(actor==2 && state==22)action=FOLEY_FIRST_CUE+FX_KAGE_BLADE;
        }
        if(same_room && action && (action!=foley_last_action[actor] || timer>foley_last_counter[actor]) &&
           timer<(state==17?8:12) && !(foley_announced&(1u<<actor))){
            /* Source takes the lowest free queue first. Start at the other
             * end and never steal a queued effect or unfinished PCM clip. */
            int c;
            for(c=2;c>=0;c--){
                FoleyVoice *v=&foley_voice[c];
                if(!v->pending && (v->mode==FOLEY_SID || (v->mode==FOLEY_PCM && v->armed==2)) &&
                   !bl_c64_read(queue[c])){
                    v->pending=action;break;
                }
            }
        }
        foley_last_action[actor]=action;foley_last_counter[actor]=timer;
    }
    if(foley_finisher_pending && same_room){
        int c;
        /* Prefer a free source voice. If all three are busy, the requested
         * finishing cry replaces voice 2; no C64 queue or game state changes. */
        for(c=2;c>=0;c--){
            FoleyVoice *v=&foley_voice[c];
            if(!v->pending && (v->mode==FOLEY_SID || (v->mode==FOLEY_PCM && v->armed==2)) &&
               !bl_c64_read(queue[c]))break;
        }
        if(c<0)c=2;
        foley_voice[c].pending=FOLEY_FIRST_CUE+FX_BRUCE_FINISH;
    }
    foley_finisher_pending=0;foley_announced=0;
}

static void foley_begin(void){
    UWORD c;
    for(c=0;c<3;c++){
        foley_voice[c]=(FoleyVoice){.period=400};
        foley_last_action[c]=foley_last_counter[c]=0;
    }
    foley_announced=0;
    foley_finisher_pending=0;
    for(c=0;c<FX_COUNT;c++)foley_variant[c]=0;
    foley_played_mask=0;foley_active=1;
    bl_c64_set_sound_observer(foley_request);
    bl_c64_set_finisher_observer(foley_finisher);
}

static void foley_stop_voice(UWORD c){
    FoleyVoice *v=&foley_voice[c];
    hw->aud[c].ac_vol=0;hw->dmacon=(UWORD)(1u<<c);
    v->stopped=line_clock();
    /* A PAL scanline exceeds 224 Paula clocks. Allow two complete periods
     * of the previous sound, including a possibly very slow SID waveform. */
    v->guard=(UWORD)(v->period/112+2);
    v->mode=FOLEY_STOPPED;
}

static void foley_end(void){
    UWORD c;
    if(!foley_active)return;
    bl_c64_set_sound_observer(0);
    bl_c64_set_finisher_observer(0);foley_finisher_pending=0;
    for(c=0;c<3;c++)if(foley_voice[c].mode!=FOLEY_SID){
        FoleyVoice *v=&foley_voice[c];
        if(v->mode!=FOLEY_STOPPED)foley_stop_voice(c);
        while(((line_clock()-v->stopped)&0xffffffUL)<v->guard){}
        source_dma.offset[c]=65535;
    }
    foley_active=0;
}

static void foley_start_sample(UWORD c,UWORD cue,UBYTE *page){
    FoleyVoice *v=&foley_voice[c];
    UWORD id=(UWORD)(cue*2+foley_variant[cue]),n=foley_samples[id].words;
    const UBYTE *input=foley_bank+foley_samples[id].offset;
    UWORD *out=(UWORD*)page;
    foley_variant[cue]^=1;
    while(n--)*out++=foley_expand[*input++];
    hw->aud[c].ac_ptr=(volatile UWORD*)page;
    hw->aud[c].ac_len=foley_samples[id].words;
    hw->aud[c].ac_per=v->period=foley_samples[id].period;
    hw->aud[c].ac_vol=foley_samples[id].volume;
    hw->intreq=(UWORD)(0x80u<<c);
    hw->dmacon=(UWORD)(DMAF_SETCLR|DMAF_MASTER|(1u<<c));
    v->mode=FOLEY_PCM;v->armed=0;
    foley_played_mask|=1UL<<id;
}

static UWORD foley_tick(UWORD *restart){
    UWORD c,reserved=0;
    for(c=0;c<3;c++){
        FoleyVoice *v=&foley_voice[c];
        UBYTE *page=source_audio_images()+c*BL_SOURCE_DMA_VOICE_BYTES;
        if(v->pending && !foley_finisher_playing(v)){
            if(v->pending!=FOLEY_RESTORE || v->mode!=FOLEY_SID){
                v->next=v->pending;
                if(v->mode!=FOLEY_STOPPED)foley_stop_voice(c);
            }
            v->pending=0;
        }
        /* PCM periods are short. Restore an ordinary SID effect on its
         * first tick (even the two-field footstep), within eight scanlines.
         * Never spin for a long outgoing SID note. */
        if(v->mode==FOLEY_STOPPED && v->next==FOLEY_RESTORE && v->guard<=8)
            while(((line_clock()-v->stopped)&0xffffffUL)<v->guard){}
        if(v->mode==FOLEY_STOPPED && ((line_clock()-v->stopped)&0xffffffUL)>=v->guard){
            if(v->next==FOLEY_RESTORE){
                hw->aud[c].ac_ptr=(volatile UWORD*)page;
                hw->aud[c].ac_len=BL_SOURCE_DMA_VOICE_BYTES/2;
                hw->intreq=(UWORD)(0x80u<<c);
                source_dma.offset[c]=65535;
                v->mode=FOLEY_SID;*restart|=(UWORD)(1u<<c);
            }else foley_start_sample(c,(UWORD)(v->next-FOLEY_FIRST_CUE),page);
        }else if(v->mode==FOLEY_PCM && v->armed<2 && (hw->intreqr&(0x80u<<c))){
            if(!v->armed){
                /* Initial LC/LEN have latched. The next IRQ marks completion. */
                hw->aud[c].ac_ptr=(volatile UWORD*)(sfx_pcm+bl_source_audio_chip_bytes()-4);
                hw->aud[c].ac_len=2;
            }
            hw->intreq=(UWORD)(0x80u<<c);++v->armed;
        }
        if(v->mode!=FOLEY_SID){
            reserved|=(UWORD)(1u<<c);
            source_voices[c].volume=0; /* Keep the waveform copier out of this page. */
        }else v->period=source_voices[c].period;
    }
    return reserved;
}
