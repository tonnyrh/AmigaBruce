/* Three source-derived voices with fixed DMA ownership and polled PAL time.
 * SID/queue rules stay in core; no DMA retrigger or one-field note gap. */
#include "../core/source_audio.h"
#include "../core/source_dma.h"
static UBYTE *sfx_pcm;
#define BL_SFX_CHIP_BYTES (bl_source_audio_chip_bytes()+BL_SOURCE_DMA_BYTES)
static BlSourceAudio source_audio;
static BlSourceDma source_dma;
static BlPaulaVoice source_voices[3];
static UBYTE source_registers[26],source_audio_active,source_audio_mode,source_audio_busy;
static ULONG source_audio_fields,source_music_fields,source_audio_hash=2166136261UL,source_music_hash=2166136261UL;
static ULONG source_clock_last,source_clock_elapsed,source_clock_missed,source_clock_max_gap;
static ULONG source_clock_starts,source_clock_pauses,source_dma_changes;
static ULONG source_clock_paused_fields,source_clock_pause_start,source_tick_max_lines;
static UBYTE source_audio_load_resume;
static UWORD source_clock_miss_fields[16],source_clock_miss_context[16];
static UWORD source_audio_context,source_clock_miss_records;
static UWORD source_voice_mask,source_dma_faults;
static UWORD source_music_faults;
static ULONG fighter_fnv(ULONG hash,UBYTE value);
static ULONG field_clock(void);
static ULONG line_clock(void);
static void source_audio_service(void);
static UBYTE *source_audio_images(void){return sfx_pcm+bl_source_audio_chip_bytes();}
static void source_audio_copy(void){
    bl_source_audio_copy(sfx_pcm);bl_source_audio_reset(&source_audio);bl_source_dma_reset(&source_dma);
}
static void source_audio_begin(void){
    UWORD c;UBYTE *images=source_audio_images();
    for(c=0;c<3;c++){
        hw->aud[c].ac_ptr=(volatile UWORD*)(images+c*BL_SOURCE_DMA_VOICE_BYTES);
        hw->aud[c].ac_len=BL_SOURCE_DMA_VOICE_BYTES/2;hw->aud[c].ac_per=400;hw->aud[c].ac_vol=0;
    }
    hw->intreq=0x0380;hw->dmacon=DMAF_SETCLR|DMAF_MASTER|7;
}
static void source_audio_mute(void){
    UWORD c;if(source_audio_active){source_clock_pause_start=field_clock();++source_clock_pauses;}
    source_audio_active=0;
    for(c=0;c<3;c++)hw->aud[c].ac_vol=0;
}
static void source_audio_resume(void){
    ULONG now=field_clock();
    if(!source_audio_active)source_clock_paused_fields+=(now-source_clock_pause_start)&0xffffffUL;
    source_clock_last=now;source_audio_active=1;
}
static void source_audio_load(long loading){
    if(loading){source_audio_load_resume=source_audio_active;if(source_audio_active)source_audio_mute();}
    else if(source_audio_load_resume){source_audio_load_resume=0;source_audio_resume();}
}
static void source_audio_output(UBYTE music){
    UWORD c,changed;ULONG *hash=music?&source_music_hash:&source_audio_hash;
    PERF_BEGIN(BL_PERF_AUDIO_RENDER);
    bl_source_audio_render(&source_audio,source_registers,source_voices);
    PERF_END(BL_PERF_AUDIO_RENDER);
    PERF_BEGIN(BL_PERF_AUDIO_DMA);
    changed=bl_source_dma_update(&source_dma,source_audio_images(),sfx_pcm,
                                bl_source_audio_chip_bytes(),source_voices);
    PERF_END(BL_PERF_AUDIO_DMA);
    PERF_BEGIN(BL_PERF_AUDIO_PUBLISH);
    if(changed&0x8000)++source_dma_faults;
    else for(c=0;c<3;c++)if(changed&(1<<c))++source_dma_changes;
    for(c=0;c<3;c++){
        const BlPaulaVoice *p=&source_voices[c];
        /* LC/LEN stay fixed until shutdown. The already prefetched Paula
         * word may contain old samples; there is no long block reload wait. */
        hw->aud[c].ac_per=p->period;hw->aud[c].ac_vol=(changed&0x8000)?0:p->volume;
        if(p->volume)source_voice_mask|=(UWORD)(1<<c);
        if(BL_AUTOTEST){
            /* Logical source parameters, not hardware LC/LEN. */
            *hash=fighter_fnv(*hash,(UBYTE)(p->offset>>8));*hash=fighter_fnv(*hash,(UBYTE)p->offset);
            *hash=fighter_fnv(*hash,(UBYTE)(p->length>>8));*hash=fighter_fnv(*hash,(UBYTE)p->length);
            *hash=fighter_fnv(*hash,(UBYTE)(p->period>>8));*hash=fighter_fnv(*hash,(UBYTE)p->period);
            *hash=fighter_fnv(*hash,(UBYTE)p->volume);
        }
    }
    if(music)++source_music_fields;else ++source_audio_fields;
    PERF_END(BL_PERF_AUDIO_PUBLISH);
}
static void source_audio_tick(void){
    ULONG start=BL_AUTOTEST?line_clock():0;
    PERF_BEGIN(BL_PERF_AUDIO_SOURCE);
    if(source_audio_mode)bl_source_audio_music(&source_audio,source_registers);
    else bl_c64_audio_frame(source_registers);
    PERF_END(BL_PERF_AUDIO_SOURCE);
    source_audio_output(source_audio_mode);
    if(BL_AUTOTEST){ULONG cost=(line_clock()-start)&0xffffffUL;if(cost>source_tick_max_lines)source_tick_max_lines=cost;}
}
static void source_audio_start(UBYTE music){
    source_audio_mode=music;source_clock_last=field_clock();++source_clock_starts;
    source_audio_active=1;source_audio_busy=1;source_audio_tick();source_audio_busy=0;
}
static void source_audio_service(void){
    ULONG now,gap;
    if(!source_audio_active || source_audio_busy)return;
    now=field_clock();gap=(now-source_clock_last)&0xffffffUL;if(!gap)return;
    source_clock_last=now;source_clock_elapsed+=gap;
    if(gap>source_clock_max_gap)source_clock_max_gap=gap;
    if(gap>1){
        source_clock_missed+=gap-1;
        if(source_clock_miss_records<16){
            source_clock_miss_fields[source_clock_miss_records]=(UWORD)(source_audio_mode?source_music_fields:source_audio_fields);
            source_clock_miss_context[source_clock_miss_records++]=(UWORD)(source_audio_context+(source_audio_mode?100:0));
        }
    }
    /* Never compress missed ticks into a burst. Keep source order and expose
     * any missed field; frequent safe draw/wait checkpoints bound normal work. */
    source_audio_busy=1;source_audio_tick();source_audio_busy=0;
}
