/* Presentation only. Poll the initial Paula DMA latch interrupt next field,
 * then replace reload registers with silence. Samples last at least95ms.
 * Never steal a busy channel (OCS needs two sample periods after stopping).
 */
#include "combat_audio_data.h"
static UBYTE *sfx_pcm;
static UBYTE sfx_busy[4],sfx_reload[4];
static UWORD sfx_sequence,sfx_kind_sequence[2];
static ULONG sfx_played,sfx_armed,sfx_dropped,sfx_variant_mask;
static void sfx_decode(void){
    UWORD i;
    for(i=0;i<BL_SFX_PCM_BYTES/2;i++){
        sfx_pcm[i*2]=(UBYTE)bl_sfx_levels[bl_sfx_packed[i]>>4];
        sfx_pcm[i*2+1]=(UBYTE)bl_sfx_levels[bl_sfx_packed[i]&15];
    }
}
static void sfx_service(void){
    UWORD c;
    for(c=0;c<4;c++)if(sfx_busy[c]){
        UWORD irq=(UWORD)(0x80U<<c);
        if(sfx_reload[c] && (hw->intreqr&irq)){
            hw->aud[c].ac_ptr=(volatile UWORD*)(sfx_pcm+BL_SFX_PCM_BYTES);
            hw->aud[c].ac_len=2;
            hw->intreq=irq;sfx_reload[c]=0;++sfx_armed;
        }
        if(!--sfx_busy[c]){
            hw->dmacon=(UWORD)(1U<<c);hw->aud[c].ac_vol=0;hw->intreq=irq;
        }
    }
}
static void sfx_play(UBYTE kind){
    static const UWORD periods[5]={422,432,443,454,465};
    UWORD c,index;
    for(c=0;c<4;c++)if(!sfx_busy[c])break;
    if(c==4){++sfx_dropped;return;}
    index=(UWORD)(kind*2+(sfx_kind_sequence[kind]++&1));
    hw->intreq=(UWORD)(0x80U<<c);
    hw->aud[c].ac_ptr=(volatile UWORD*)(sfx_pcm+bl_sfx_offsets[index]);
    hw->aud[c].ac_len=bl_sfx_lengths[index]/2;
    hw->aud[c].ac_per=periods[sfx_sequence%5];
    hw->aud[c].ac_vol=(UWORD)(kind?48:40);
    sfx_busy[c]=10;sfx_reload[c]=1;++sfx_sequence;++sfx_played;
    sfx_variant_mask|=1UL<<index;
    hw->dmacon=(UWORD)(DMAF_SETCLR|DMAF_MASTER|(1U<<c));
}
