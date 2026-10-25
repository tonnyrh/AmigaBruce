/* Paula backend for source-derived SID registers. Three persistent DMA voices,
 * immutable short wave cycles; no per-hit PCM decoding or busy-channel drops. */
#include "../core/source_audio.h"
static UBYTE *sfx_pcm;
#define BL_SFX_CHIP_BYTES (bl_source_audio_chip_bytes())
static BlSourceAudio source_audio;
static BlPaulaVoice source_voices[3];
static UBYTE source_registers[26];
static ULONG source_audio_fields,source_music_fields,source_audio_hash=2166136261UL,source_music_hash=2166136261UL;
static UWORD source_voice_mask;
static UWORD source_music_faults;
static ULONG fighter_fnv(ULONG hash,UBYTE value);
static void source_audio_copy(void){bl_source_audio_copy(sfx_pcm);bl_source_audio_reset(&source_audio);}
static void source_audio_begin(void){
    UWORD c;
    for(c=0;c<3;c++){
        hw->aud[c].ac_ptr=(volatile UWORD*)(sfx_pcm+BL_SFX_CHIP_BYTES-4);
        hw->aud[c].ac_len=2;hw->aud[c].ac_per=400;hw->aud[c].ac_vol=0;
    }
    hw->intreq=0x0380;hw->dmacon=DMAF_SETCLR|DMAF_MASTER|7;
}
static void source_audio_mute(void){UWORD c;for(c=0;c<3;c++)hw->aud[c].ac_vol=0;}
static void source_audio_output(UBYTE music){
    UWORD c;ULONG *hash=music?&source_music_hash:&source_audio_hash;
    bl_source_audio_render(&source_audio,source_registers,source_voices);
    for(c=0;c<3;c++){
        const BlPaulaVoice *p=&source_voices[c];
        hw->aud[c].ac_ptr=(volatile UWORD*)(sfx_pcm+p->offset);
        hw->aud[c].ac_len=p->length/2;hw->aud[c].ac_per=p->period;hw->aud[c].ac_vol=p->volume;
        if(p->volume)source_voice_mask|=(UWORD)(1<<c);
        /* Test-only signature of the actual hardware parameters; silence and
         * continuous waves have no one-shot reload interrupt contract. */
        if(BL_AUTOTEST){
            *hash=fighter_fnv(*hash,(UBYTE)(p->offset>>8));*hash=fighter_fnv(*hash,(UBYTE)p->offset);
            *hash=fighter_fnv(*hash,(UBYTE)(p->length>>8));*hash=fighter_fnv(*hash,(UBYTE)p->length);
            *hash=fighter_fnv(*hash,(UBYTE)(p->period>>8));*hash=fighter_fnv(*hash,(UBYTE)p->period);
            *hash=fighter_fnv(*hash,(UBYTE)p->volume);
        }
    }
    if(music)++source_music_fields;else ++source_audio_fields;
}
