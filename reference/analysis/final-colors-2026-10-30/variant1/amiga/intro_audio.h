/* Startup voice only; the second game bitmap is temporary Paula storage.
 * Stop DMA and wait two sample periods before restoring that bitmap.
 */
#include "intro_audio_data.h"
static void intro_decode(UBYTE *dst){
    LONG predictor=0;int index=0;
    ULONG n;
    for(n=0;n<BL_INTRO_PCM_BYTES;n++){
        UBYTE packed=bl_intro_packed[n>>1];
        UBYTE code=(UBYTE)((n&1)?packed&15:packed>>4);
        LONG step=bl_intro_steps[index],delta=step>>3;
        if(code&4)delta+=step;
        if(code&2)delta+=step>>1;
        if(code&1)delta+=step>>2;
        predictor+=(code&8)?-delta:delta;
        if(predictor>32767)predictor=32767;
        if(predictor< -32768)predictor= -32768;
        index+=bl_intro_index[code&7];
        if(index<0)index=0;
        if(index>88)index=88;
        dst[n]=(UBYTE)(predictor>>8);
    }
    for(n=0;n<4;n++)dst[BL_INTRO_PCM_BYTES+n]=0;
}
